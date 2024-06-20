from typing import Optional
import hikari.commands
import lightbulb
import mysql.connector
from mysql.connector import Error
import hikari
from datetime import datetime
from dotenv import load_dotenv
import os

import mysql.connector.cursor

# Load environment variables from .env file
load_dotenv()


class Order(int):
    DATE_ASC = 0
    DATE_DESC = 1


def time_since(dt):
    """
    Calculates the time difference between a given datetime (dt) and the current time.
    Returns a human-readable string indicating how long ago the datetime occurred.

    Parameters:
    - dt: A datetime object representing the timestamp to compare with the current time (e.g., "2024-06-16 15:11:55").

    Returns:
    - A string indicating the time difference in a human-readable format (e.g., "X days ago").
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


async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    plugin: lightbulb.Plugin,
) -> list[hikari.commands.CommandChoice]:
    query: str = opt.value        # The current input in the message field.
    user_id = inter.user.id       # The user ID

    # The database cursor
    cursor: mysql.connector.cursor.MySQLCursor = plugin.app.d.cursor

    history: list[hikari.commands.CommandChoice] = []

    try:
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
        result = cursor.fetchall()
        # Debugging: print the result
        # print("Query Result:", result)

        for row in result:
            # print("Row:", row)  # Debugging: print each row
            fa_id = row[0]
            fa_name = row[1]
            updated_at = row[2]
            # print(f'{fa_name}\n{updated_at}')

            time_ago = time_since(updated_at)

            formatted_template = f"{fa_name} ~ {time_ago}"

            choice = hikari.commands.CommandChoice(
                name=formatted_template,
                value=str(fa_id)
                )
            history.append(choice)
    except Error as e:
        print(f'Retrieving Data Unsucessfully: {e}')

    if history == []:
        choice = hikari.commands.CommandChoice(
            name="No past FA data found.",
            value="0"
        )
        return [choice]

    return history[:25]
