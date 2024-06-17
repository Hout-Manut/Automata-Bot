from typing import Optional
import mysql.connector
from mysql.connector import Error
import hikari
from datetime import datetime
from dotenv import load_dotenv
import os

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
    print(f'diff: {diff}\nsec: {seconds}')
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{int(minutes)} minutes ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{int(hours)} hours ago"
    else:
        days = seconds // 86400
        return f"{int(days)} days ago"
    
async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    sort_by: Optional[int] = Order.DATE_DESC,
) -> list[str]:
    query: str = opt.value      # The current input in the message field.
    user_id = inter.user.id     # The user ID
    
    history: list[str] = []
    
    # TODO : Get history from db using user_id, sorted.
    try:
        db_con = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            # port=1201
        )
        
        if db_con.is_connected():
            try:
                cursor = db_con.cursor()

                sql_query = 'SELECT fa_name, updated_at FROM Recent WHERE user_id=%s;'
                cursor.execute(sql_query, (user_id,))
                result = cursor.fetchall()
                # Debugging: print the result
                print("Query Result:", result)

                for row in result:
                    print("Row:", row)  # Debugging: print each row
                    fa_name = row[0]
                    updated_at = row[1]
                    print(f'{fa_name}\n{updated_at}')

                    time_ago = time_since(updated_at)

                    formatted_template = f"{fa_name} ~ {time_ago}"
                    history.append(formatted_template)
            except Error as e:
                print(f'Retrieving Data Unsucessfully: {e}')

    except Error as e:
        print(f'Error: {e}')

    return history[:25]
