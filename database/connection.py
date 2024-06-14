import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        db_con = mysql.connector.connect(
            host='localhost',
            user='root',
            password='ur password',
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

def select_data(db_con):
    try:
        cursor = db_con.cursor()
        sql_query = 'SELECT * FROM History'
        cursor.execute(sql_query)
        for row in cursor:
            print(row)
    except Error as e:
        print(f'Error selecting data: {e}')

def update_data(db_con, user_id, new_fa_name, new_alphabet):
    try:
        cursor = db_con.cursor()
        sql_query = 'UPDATE History SET fa_name=%s, alphabet=%s WHERE user_id=%s'
        update_data = (new_fa_name, new_alphabet, user_id)
        cursor.execute(sql_query, update_data)
        db_con.commit()
        print('Data updated successfully')
    except Error as e:
        print(f'Error updating data: {e}')

def delete_data(db_con, user_id):
    try:
        cursor = db_con.cursor()
        sql_query = 'DELETE FROM History WHERE user_id=%s'
        cursor.execute(sql_query, (user_id,))
        db_con.commit()
        print('Data deleted successfully')
    except Error as e:
        print(f'Error deleting data: {e}')

# Usage
db_con = connect_to_database()
if db_con:
    # Insert data
    # {'q0', 'q1', 'q2'}, {'a', 'b'}, 'q0', {q1}, 'q0,a=q1', '2024-06-13'

    insert_data(
        db_con,
        3,
        'Finite Automaton',
        'q0 q1 q2',  # " ".join(modal.fa.states)
        'a b',
        'q0',
        'q1',
        'q0,a->q1',
        '2024-06-13')

    # Select data
    select_data(db_con)

    # Update data
    # update_data(db_con, 3, 'Updated Automaton', 'a,b,c')

    # # Delete data
    # delete_data(db_con, 3)
