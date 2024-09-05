import os, csv, re, collections, codecs
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import sessionmaker

from .config import main_config

# Create a named tuple to hold the database components
DB = collections.namedtuple("DB", ["db_url", "engine", "metadata", "Session", "session"])


def create_db_connection():
    db_url = main_config.get("data", "db_url")
    engine = create_engine(db_url)
    metadata = MetaData()
    Session = sessionmaker(bind=engine)
    session = Session()
    return DB(db_url, engine, metadata, Session, session)


# Initialize the db object
db = create_db_connection()

def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())


class Writer:
    def __init__(self):
        self.remote = main_config.get("data", "remote_dir")
        self.table_mapping = {}  # Map of table_name -> Table object

    def drop_th_tables(self):
        """Drops all tables from the database that start with 'thstore_'."""
        # Reflect the current database state to get all tables
        db.metadata.reflect(bind=db.engine)

        # Iterate over all tables in the metadata
        for table_name in db.metadata.tables:
            if table_name.startswith("thstore_"):
                # Drop the table
                table = db.metadata.tables[table_name]
                print(f"Dropping table: {table_name}")
                table.drop(db.engine)

        # Clear the metadata cache after dropping tables
        db.metadata.clear()
        print("Dropped all tables starting with 'thstore_'.")


    def create_table_from_csv(self, file_path, table_name):
        """Creates a SQL table dynamically from a CSV file."""
        print(f"\ncreating table from {file_path} as {table_name}")

        with codecs.open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            # Get the columns (first row of the CSV)
            columns = next(reader)
            columns = [clean_name(col_name) for col_name in columns]

            # Define the SQL table dynamically with all columns as Strings
            table = Table(
                table_name,
                db.metadata,
                *[Column(col_name, String) for col_name in columns]
            )
            table.create(db.engine)

            # Insert each row into the table
            with db.engine.connect() as conn:
                for row in reader:
                    insert_stmt = table.insert().values(dict(zip(columns, row)))
                    conn.execute(insert_stmt)

            return table


    def ingest_all(self):
        """Iterates over CSV files in the remote directory and ingests them."""
        self.drop_th_tables()
        csv_dir = os.path.join(self.remote, "csv")

        # Iterate over all CSV files in the directory
        for csv_file in os.listdir(csv_dir):
            if csv_file.endswith('.csv'):
                file_path = os.path.join(csv_dir, csv_file)
                table_name = os.path.splitext(csv_file)[0]
                # TODO: allow changing prefix
                table_name = f"thstore_{clean_name(table_name)}"

                # Create a SQL table and insert data from the CSV file
                table = self.create_table_from_csv(file_path, table_name)

                # Store the table in the mapping
                self.table_mapping[table_name] = table

        print("Ingested all CSV files and created tables.")
