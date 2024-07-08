"""
This module is used to get user's recent FA datas to fill in the recent option in most commands so they can select them there.
"""
from typing import Callable

import hikari
from hikari.commands import CommandChoice
import lightbulb
from datetime import datetime
from mysql.connector import Error as SQLError
from mysql.connector.cursor import MySQLCursor, RowType

from bot.automata.classes import RegexPatterns


class NoItemsFoundError(Exception):
    pass


ProcessedQueryT = dict[str, str | tuple[str, int] | set[str] | None]
"""
Type alias for processed query.

It is a dictionary that holds the result of processing a query. The keys are the type of the query and the values are the result of that query.

The types of the queries are:
- fa_type: str
- state_num: tuple[str, int]
- alphabet_num: tuple[str, int]
- alphabets: set[str]
- Each value can be None, meaning that the query did not specify that option.
"""
ProcessedQueryItemT = str | tuple[str, int] | set[str] | None

query_cache: dict[int, list[RowType]] = {}


async def cache(
    user_id: int,
    rows: list[RowType]
) -> None:
    query_cache[user_id] = rows


async def clear_cache() -> None:
    query_cache.clear()


def time_since(dt: datetime) -> str:
    """
    Calculates the time difference between a given datetime (dt) and the current time.
    Returns a human-readable string indicating how long ago the datetime occurred.

    Args:
        dt (str): A datetime object representing the timestamp to compare with the current time (e.g., "2024-06-16 15:11:55").

    Returns:
        A string indicating the time difference in a human-readable format (e.g., "X days ago").
    """
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        s = "" if seconds == 1 else "s"
        return f"{int(seconds)} second{s} ago"
    elif seconds < 3600:
        minutes = seconds // 60
        s = "" if minutes == 1 else "s"
        return f"{int(minutes)} minute{s} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        s = "" if hours == 1 else "s"
        return f"{int(hours)} hour{s} ago"
    else:
        days = seconds // 86400
        s = "" if days == 1 else "s"
        return f"{int(days)} day{s} ago"


async def get_all_fa(
    cursor: MySQLCursor,
    user_id: int,
) -> list[CommandChoice]:
    history: list[CommandChoice] = []

    sql_query = """
    SELECT
        id,
        fa_name,
        updated_at
    FROM Recent
    WHERE user_id=%s
    ORDER BY updated_at DESC;
    """
    cursor.execute(sql_query, (user_id,))
    rows = cursor.fetchall()
    for row in rows:
        fa_id = row[0]
        fa_name = row[1]
        updated_at = row[2]

        time_ago = time_since(updated_at)

        formatted_template = f"{fa_name} ~ {time_ago}"

        choice = CommandChoice(
            name=formatted_template,
            value=str(fa_id),
        )
        history.append(choice)
    return history


def filter(): ...


async def get_full_fa(
    cursor: MySQLCursor,
    user_id: int,
) -> list[RowType] | None:
    if user_id in query_cache:
        return query_cache[user_id]

    sql_query = """
        SELECT
            id,
            fa_name,
            states,
            alphabets,
            initial_state,
            final_states,
            transitions,
            updated_at
        FROM Recent
        WHERE user_id=%s
        ORDER BY updated_at DESC;
        """
    cursor.execute(sql_query, (user_id,))
    rows = cursor.fetchall()
    return rows[:25]


def process_query(
    query: str
) -> ProcessedQueryT:
    queries: ProcessedQueryT = {
        "fa_type": None,
        "state_num": None,
        "alphabet_num": None,
        "alphabets": None,
    }

    dfa_or_nfa = RegexPatterns.DFA_OR_NFA.search(query)
    if dfa_or_nfa:
        queries["fa_type"] = dfa_or_nfa.group(1)

    state_num_match = RegexPatterns.STATE_NUM_QUERY.search(query)
    if state_num_match:
        operator = state_num_match.group(1)
        state_num = state_num_match.group(2)
        queries["state_num"] = (operator, int(state_num))

    alphabet_num_match = RegexPatterns.ALPHABET_NUM_QUERY.search(query)
    if alphabet_num_match:
        operator = alphabet_num_match.group(2)
        alphabet_num = alphabet_num_match.group(3)
        queries["alphabet_num"] = (operator, int(alphabet_num))

    alphabets_match = RegexPatterns.ALPHABETS_QUERY.search(query)
    if alphabets_match:
        alphabets = alphabets_match.group(2)
        queries["alphabets"] = set(alphabets)


    return queries



async def find_some_fa(
    query: str,
    cursor: MySQLCursor,
    user_id: int,
) -> list[CommandChoice]:
    history: list[CommandChoice] = []
    query = query.lower()

    rows = await get_full_fa(cursor, user_id)

    if not rows:
        return history

    processed_query = process_query(query)
    try:
        if processed_query["fa_type"]:
            rows = filter_fa(rows, processed_query["fa_type"])

        if processed_query["state_num"]:
            rows = filter_state_nums(rows, processed_query["state_num"])

        if processed_query["alphabet_num"]:
            rows = filter_alphabet_nums(rows, processed_query["alphabet_num"])

        elif processed_query["alphabets"]: # TODO: Make these 2 works tgt
            rows = filter_alphabets(rows, processed_query["alphabets"])

    except NoItemsFoundError:
        choice = CommandChoice(
            name="No FA data found for that query.",
            value="0",
        )
        return [choice]

    for row in rows:
        fa_id = row[0]
        fa_name = row[1]
        updated_at = row[7]

        time_ago = time_since(updated_at)

        formatted_template = f"{fa_name} ~ {time_ago}"

        choice = CommandChoice(
            name=formatted_template,
            value=str(fa_id),
        )
        history.append(choice)
    return history


def row_check(func: Callable[[list[RowType], ProcessedQueryItemT], list[RowType]]):

    def wrapper(rows: list[RowType], filter_query: ProcessedQueryItemT) -> list[RowType]:
        if not rows:
            raise NoItemsFoundError
        return func(rows, filter_query)

    return wrapper

@row_check
def filter_fa(
    rows: list[RowType],
    filter_fa: str
    ) -> list[RowType]:
    filtered = [row for row in rows if filter_fa in row[1].lower()]

    return filtered


@row_check
def filter_state_nums(
    rows: list[RowType],
    state_nums: tuple[str, int]
    ) -> list[RowType]:
    filtered = []

    if state_nums[0] == ">":
        for row in rows:
            states = row[2].split()
            db_state_nums = len(states)
            if state_nums[1] < db_state_nums:
                filtered.append(row)

    elif state_nums[0] == "<":
        for row in rows:
            states = row[2].split()
            db_state_nums = len(states)
            if state_nums[1] > db_state_nums:
                filtered.append(row)

    elif state_nums[0] == ">=":
        for row in rows:
            states = row[2].split()
            db_state_nums = len(states)
            if state_nums[1] <= db_state_nums:
                filtered.append(row)

    elif state_nums[0] == "<=":
        for row in rows:
            states = row[2].split()
            db_state_nums = len(states)
            if state_nums[1] >= db_state_nums:
                filtered.append(row)

    elif state_nums[0] == "=":
        for row in rows:
            states = row[2].split()
            db_state_nums = len(states)
            if state_nums[1] == db_state_nums:
                filtered.append(row)

    return filtered


@row_check
def filter_alphabet_nums(
    rows: list[RowType],
    state_nums: tuple[str, int]
) -> list[RowType]:
    filtered = []

    if state_nums[0] == ">":
        for row in rows:
            alphabets = row[3].split()
            db_alphabet_nums = len(alphabets)
            if state_nums[1] < db_alphabet_nums:
                filtered.append(row)

    elif state_nums[0] == "<":
        for row in rows:
            alphabets = row[3].split()
            db_alphabet_nums = len(alphabets)
            if state_nums[1] >= db_alphabet_nums:
                filtered.append(row)

    elif state_nums[0] == ">=":
        for row in rows:
            alphabets = row[3].split()
            db_alphabet_nums = len(alphabets)
            if state_nums[1] < db_alphabet_nums:
                filtered.append(row)

    elif state_nums[0] == "<=":
        for row in rows:
            alphabets = row[3].split()
            db_alphabet_nums = len(alphabets)
            if state_nums[1] >= db_alphabet_nums:
                filtered.append(row)

    elif state_nums[0] == "=":
        for row in rows:
            alphabets = row[3].split()
            db_alphabet_nums = len(alphabets)
            if state_nums[1] == db_alphabet_nums:
                filtered.append(row)

    return filtered


@row_check
def filter_alphabets(
    rows: list[RowType],
    alphabets: set[str]
) -> list[RowType]:
    filtered = [row for row in rows if alphabets <= set(row[3].split())]
    return filtered



async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    plugin: lightbulb.Plugin,
) -> list[CommandChoice]:
    user_id = inter.user.id
    query = opt.value

    cursor: MySQLCursor = plugin.app.d.cursor
    history: list[CommandChoice] = []

    try:
        if query:
            history = await find_some_fa(query, cursor, user_id)
        else:
            history = await get_all_fa(cursor, user_id)
        # history = await get_all_fa(cursor, user_id)
    except SQLError as e:
        print(f'Retrieving Data Unsucessfully: {e}')
        choice = CommandChoice(
            name="An error occurred",
            value="0",
        )
        return [choice]

    if history == []:
        choice = CommandChoice(
            name="No past FA data found.",
            value="0",
        )
        return [choice]

    return history[:25]
