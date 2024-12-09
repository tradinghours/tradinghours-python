import sqlite3
import pandas as pd



# TODO: consider using store.DB
def read_sqlite_tables_to_dict(db_path, tables=None):
    """
    Reads all tables from a SQLite database and returns a dictionary where
    the keys are the table names and the values are pandas DataFrames containing the table data.

    Parameters:
    db_path (str): The path to the SQLite database file.

    Returns:
    dict: A dictionary with table names as keys and DataFrames as values.
    """
    dataframes_dict = {}
    with sqlite3.connect(db_path) as conn:
        # Retrieve the list of table names from the database
        table_names = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
        # Read each table into a DataFrame
        for table_name in table_names['name']:
            if table_name.startswith("sqlite"): continue
            if not tables is None and table_name not in tables:
                continue

            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            dataframes_dict[table_name] = df
            print(f"Data loaded from table '{table_name}' into DataFrame.")
    return dataframes_dict
