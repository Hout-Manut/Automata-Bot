import os

import dotenv
import mysql.connector
from mysql.connector import Error, InterfaceError


if __name__ == "__main__":
    dotenv.load_dotenv()

    try:
        db_con = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
    except InterfaceError:
        print("Database connection failed. Please check your environment variables.")
        exit()
    except Error as e:
        print(f"Setup failed: {e}")
        exit()

    if db_con.is_connected():
        print("Database connection established. Setting up...")

        cursor = db_con.cursor()
        cursor.execute("SHOW DATABASES")

        if "Automata" in [x[0] for x in cursor]:
            print("Automata database already exists. Do you want to overwrite it? (y/n)")
            opt = input()
            if "y" in opt:
                cursor.execute("DROP DATABASE Automata")
            else:
                print("Setup cancelled.")
                exit()

        cursor.execute("CREATE DATABASE Automata")
        cursor.execute("USE Automata")

        cursor.execute("""
        CREATE TABLE Recent (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id bigint,
            fa_name VARCHAR(255),
            states VARCHAR(255),
            alphabets VARCHAR(255),
            initial_state VARCHAR(255),
            final_states VARCHAR(255),
            transitions VARCHAR(255),
            updated_at DATETIME
        );""")

        print("Setup complete. You can now use the bot.")
    else:
        print("Database connection failed. Please check your environment variables.")
