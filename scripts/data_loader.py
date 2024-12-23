import csv
import os
import sqlite3
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

data_csv_path = BASE_DIR / 'data' / 'ingredients.csv'

# Paths for SQLite
sqlite_db_path = BASE_DIR / 'backend' / 'db.sqlite3'

# PostgreSQL connection settings
pg_host = 'localhost'  # Use locally
pg_port = os.getenv('DB_PORT', '5432')
pg_dbname = os.getenv('POSTGRES_DB', 'your_db')
pg_user = os.getenv('POSTGRES_USER', 'your_user')
pg_password = os.getenv('POSTGRES_PASSWORD', 'your_password')
db_type = os.getenv('DB_TYPE', 'sqlite')


def db_connection(func):
    """
    Decorator to manage the database connection.
    Detects whether to use SQLite or PostgreSQL.
    """

    def wrapper(*args, **kwargs):
        if db_type.lower() == 'postgresql':
            connection = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                dbname=pg_dbname,
                user=pg_user,
                password=pg_password,
            )
        else:  # Default to SQLite
            connection = sqlite3.connect(sqlite_db_path)

        cursor = connection.cursor()
        try:
            result = func(cursor=cursor, *args, **kwargs)
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()
        return result

    return wrapper


def read_csv(file_path: str):
    """
    Reads a CSV file and returns its content as a tuple of rows.
    """
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        data = []
        for row in reader:
            row[0] = row[0].capitalize()
            data.append(tuple(row))
    if not data:
        raise ValueError('CSV file is empty or not formatted correctly.')
    return data


@db_connection
def load_data(cursor, data: tuple):
    """
    Loads data into the `recipes_ingredient` table.
    """
    if not data:
        raise ValueError('No data to insert.')

    insert_query = (
        (
            'INSERT INTO recipes_ingredient (name, measurement_unit) VALUES (%s, %s)'
        )
        if isinstance(cursor, psycopg2.extensions.cursor)
        else (
            'INSERT INTO recipes_ingredient (name, measurement_unit) VALUES (?, ?)'
        )
    )
    cursor.executemany(insert_query, data)


if __name__ == '__main__':
    try:
        data = read_csv(data_csv_path)
        load_data(data=data)  # type: ignore
        print('Data has been successfully loaded into the database.')
    except Exception as exception:
        print('Encountered error:', exception)
