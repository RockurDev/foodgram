import csv
import sqlite3

data_csv_path = 'data/ingredients.csv'
db_path = 'backend/db.sqlite3'


def db_connection(func):
    """
    Decorator to manage the database connection.
    Ensures the connection is opened and closed properly.
    """

    def wrapper(*args, **kwargs):
        connection = sqlite3.connect(db_path)
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
def load_data(cursor: sqlite3.Cursor, data: tuple[str]):
    """
    Loads data into the `recipes_ingredient` table.
    """
    if not data:
        raise ValueError('No data to insert.')
    insert_query = (
        'INSERT INTO recipes_ingredient (name, measurement_unit) VALUES (?, ?)'
    )
    cursor.executemany(insert_query, data)


if __name__ == '__main__':
    try:
        data = read_csv(data_csv_path)
        load_data(data=data)  # type: ignore
        print('Data has been successfully loaded into the database.')
    except Exception as exception:
        print('Encountered error:', exception)
