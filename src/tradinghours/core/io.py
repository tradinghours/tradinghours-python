import os, sqlite3
from pathlib import Path
from .utils import slugify, set_types
import pandas as pd

"""

- know the columns
- data types
- csv/sqlite files

"""

def df_data_from_csvs(folder=None, files=None):
    """
    Only used for --no-download option
    """
    if folder:
        files = [Path(folder) / f for f in os.listdir(folder)]

    data = {}
    for file in files:
        title = slugify(file.stem)
        data[title] = pd.read_csv(file)

    return data


def df_data_from_sql(db_path, tables=None):
    """
    Reads all tables from a SQLite database and returns a dictionary where
    the keys are the table names and the values are pandas DataFrames containing the table data.

    Parameters:
    db_path (str): The path to the SQLite database file.

    Returns:
    dict: A dictionary with table names as keys and DataFrames as values.
    """
    data = {}
    with sqlite3.connect(db_path) as conn:
        # Retrieve the list of table names from the database
        table_names = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
        # Read each table into a DataFrame
        for table_name in table_names['name']:
            if table_name.startswith("sqlite"): continue
            if not tables is None and table_name not in tables:
                continue

            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            data[table_name] = df

    data = set_types(data)
    return data


def save_data_to_sql(db_path, data):
    with sqlite3.connect(db_path) as conn:
        for table_name, df in data.items():
            try:
                df.to_sql(table_name, conn, if_exists="replace", index=False)
            except Exception as e:
                print(f"Failed to save table '{table_name}': {e}")
