import mysql.connector
from mysql.connector import Error

try:
    db_con = mysql.connector.connect(
        host='localhost',
        user='root',
        password='ur password',
        database='Automata'
    )

    if db_con.is_connected():
        # Debug
        print('Database is established')

        cursor = db_con.cursor()

        sql_query = 'INSERT INTO History (user_id, fa_name, state, alphabet, initial_state, final_state, transition, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        # sql_query = 'SELECT * FROM History WHERE user_id = %s;'
        # sql_query = 'UPDATE History SET fa_name=%s, alphabet=%s WHERE user_id=%s;'
        # sql_query = 'DELETE FROM History WHERE user_id=%s'
        # sql_query = 'SELECT * FROM History;'

        insert_data = (
            3,  # user_id
            'Finite Automaton',  # fa_name
            'q0',  # state
            'a,b',  # alphabet
            'q0',  # initial_state
            'q1',  # final_state
            'q0,a->q1',  # transition
            '2024-06-13'  # updated_at
        )

        cursor.execute(sql_query, insert_data)
        # cursor.execute(sql_query, (1,))
        # cursor.execute(sql_query)

        db_con.commit()

        for row in cursor:
            print(row)

except Error as e:
    print(f'Error: {e}')

