from typing import Optional
import mysql.connector
from mysql.connector import Error
import hikari


class Order(int):
    DATE_ASC = 0
    DATE_DESC = 1

def connect_to_database():
    try:
        db_con = mysql.connector.connect(
            host='localhost',
            user='root',
            password='limhao',
            database='Automata'
        )
        if db_con.is_connected():
            print('Database connection established')
            return db_con
    except Error as e:
        print(f'Error connecting to database: {e}')
        return None
    
def insert_data(db_con, user_id, fa_name, state, alphabet, initial_state, final_state, transition, updated_at):
    try:
        cursor = db_con.cursor()
        sql_query = 'INSERT INTO History (user_id, fa_name, state, alphabet, initial_state, final_state, transition, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        insert_data = (user_id, fa_name, state, alphabet, initial_state, final_state, transition, updated_at)
        cursor.execute(sql_query, insert_data)
        db_con.commit()
        print('Data inserted successfully')
    except Error as e:
        print(f'Error inserting data: {e}')
        
async def history_autocomplete(
    opt: hikari.AutocompleteInteractionOption,
    inter: hikari.AutocompleteInteraction,
    sort_by: Optional[int] = Order.DATE_DESC,
) -> list[str]:
    query: str = opt.value      # The current input in the message field.
    user_id = inter.user.id     # The user ID
    
    history: list[str] = []
    
    # TODO : Get history from db using user_id, sorted.


    return history[:25]
