"""
This module is used to get user's recent FA datas to fill in the recent option in most commands so they can select them there.
"""

import hikari
import hikari.commands
import lightbulb
from datetime import datetime
from mysql.connector import Error
import mysql.connector.cursor


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


async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    plugin: lightbulb.Plugin,
) -> list[hikari.commands.CommandChoice]:
    user_id = inter.user.id
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

        for row in result:
            fa_id = row[0]
            fa_name = row[1]
            updated_at = row[2]

            time_ago = time_since(updated_at)

            formatted_template = f"{fa_name} ~ {time_ago}"

            choice = hikari.commands.CommandChoice(
                name=formatted_template,
                value=str(fa_id)
                )
            history.append(choice)
    except Error as e:
        print(f'Retrieving Data Unsucessfully: {e}')
        choice = hikari.commands.CommandChoice(
            name="An error occurred",
            value="0",
        )
        return [choice]

    if history == []:
        choice = hikari.commands.CommandChoice(
            name="No past FA data found.",
            value="0",
        )
        return [choice]

    return history[:25]  # Discord only allows up to 25 items.
