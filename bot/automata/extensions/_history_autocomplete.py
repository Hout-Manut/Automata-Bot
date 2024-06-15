from typing import Optional
import mysql.connector
from mysql.connector import Error
import hikari


class Order(int):
    DATE_ASC = 0
    DATE_DESC = 1
        
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
            host='localhost',
            user='root',
            password='limhao',
            database='Automata'
        )
        
        if db_con.is_connected():
            try:
                cursor = db_con.cursor()

                sql_query = 'SELECT fa_name FROM Recent WHERE user_id=%s;'
                cursor.execute(sql_query, (user_id,))
                result = cursor.fetchall()
                print(result)
                for row in result:
                #     print(row)
                    history.append(row[0])
            except Error as e:
                print(f'Retrieving Data Unsucessfully: {e}')

    except Error as e:
        print(f'Error: {e}')

    return history[:25]
