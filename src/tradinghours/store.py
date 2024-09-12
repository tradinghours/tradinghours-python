import os, csv, re, codecs
import datetime as dt
from pathlib import Path
from pprint import pprint
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .config import main_config
from .client import get_json as client_get_json, get_remote_timestamp as client_get_remote_timestamp
from .util import tprefix, tname, clean_name
from .exceptions import DBError

class DB:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = self = super().__new__(cls)
            self.db_url = main_config.get("data", "db_url")
            self.engine = create_engine(self.db_url)
            self.metadata = MetaData()
            try:
                self.update_metadata()
            except Exception:
                self._failed_to_access = True

            self.Session = sessionmaker(bind=self.engine)
            # self.session = self.Session()

        return cls._instance

    def table(self, table_name):
        return self.metadata.tables[tname(table_name)]

    def ready(self):
        if getattr(self, "_failed_to_access", True):
            raise DBError("Could not access database")

        if tname("admin") not in self.metadata.tables:
            raise DBError("Database not prepared. Did you run `tradinghours import`?")

    @contextmanager
    def session(self):
        s = self.Session()
        yield s
        s.close()

    def execute(self, *query):
        with self.session() as s:
            result = s.execute(*query)
            s.commit()
            return result

    def query(self, *query):
        with self.session() as s:
            return s.query(*query)


    def get_local_timestamp(self):
        if tname("admin") not in self.metadata.tables:
            return

        table = self.table("admin")
        with self.session() as s:
            result = s.query(
                table.c["data_timestamp"]).order_by(
                    table.c["id"].desc()).first()
            if result:
                return result[0].replace(tzinfo=dt.UTC)

    def needs_download(self):
        if local := self.get_local_timestamp():
            remote_timestamp = client_get_remote_timestamp()
            return remote_timestamp > local
        return True

    def update_metadata(self):
        self.metadata.clear()
        self.metadata.reflect(bind=self.engine)
        self._failed_to_access = False

db = DB()

class Writer:

    def __init__(self):
        self.remote = Path(main_config.get("data", "remote_dir"))

    def prepare_th_admin(self):
        """Preserves the last 9 records from the thstore_admin table,
        drops the table, recreates it, and re-inserts the 9 records."""
        table_name = tname("admin")
        table_exists = table_name in db.metadata.tables
        last_9_records = []

        if table_exists:
            table = db.metadata.tables[table_name]
            columns_to_select = [col for col in table.c.values() if col.name != 'id']
            result = db.execute(
                table.select()
                .with_only_columns(*columns_to_select)
                .order_by(table.c['id'].desc())
                .limit(9)
            )

            # Fetch all results
            last_9_records = result.fetchall()
            last_9_records = [
                {col.name: value for col, value in zip(columns_to_select, row)}
                for row in last_9_records[::-1]
            ]
            table.drop(db.engine)
            db.metadata.clear()

        table = Table(
            table_name,
            db.metadata,
            Column('id', Integer, primary_key=True),
            Column('data_timestamp', DateTime, nullable=False),
            Column('access_level', String, nullable=False),
            Column('download_timestamp', DateTime, nullable=False),
        )
        table.create(db.engine)
        if last_9_records:
            db.execute(table.insert(), last_9_records)

        db.update_metadata()

    def drop_th_tables(self):
        """Drops all tables from the database that start with 'thstore_'."""
        # Iterate over all tables in the metadata
        for table_name in db.metadata.tables:
            if table_name.startswith(tprefix) and "admin" not in table_name:
                table = db.metadata.tables[table_name]
                table.drop(db.engine)

        # Clear the metadata cache after dropping tables
        db.update_metadata()
        # print(f"Dropped all tables starting with {tprefix}.")


    def create_table_from_csv(self, file_path, table_name):
        """Creates a SQL table dynamically from a CSV file."""

        with codecs.open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            # Get the columns (first row of the CSV)
            columns = next(reader)
            columns = [clean_name(col_name) for col_name in columns]

            # Define the SQL table dynamically with all columns as Strings
            table = Table(
                table_name,
                db.metadata,
                Column('id', Integer, primary_key=True),
                *[Column(col_name, String) for col_name in columns]
            )
            batch = []
            for row in reader:
                batch.append(dict(zip(columns, row)))

        table.create(db.engine)
        db.execute(table.insert(), batch)
        return table

    def update_admin(self, access_level):
        version_file = self.remote / "VERSION.txt"
        timestamp_format = "Generated at %a, %d %b %Y %H:%M:%S %z"
        content = version_file.read_text()
        line = content.splitlines()[0]
        data_timestamp = dt.datetime.strptime(line, timestamp_format)

        db.execute(
            db.table("admin").insert().values(
                data_timestamp=data_timestamp,
                access_level=access_level,
                download_timestamp=dt.datetime.now(dt.UTC).replace(tzinfo=None)
            )
        )

    def ingest_all(self):
        """Iterates over CSV files in the remote directory and ingests them."""
        self.prepare_th_admin()
        self.drop_th_tables()
        csv_dir = self.remote / "csv"

        # Iterate over all CSV files in the directory
        for csv_file in os.listdir(csv_dir):
            if csv_file.endswith('.csv'):
                file_path = csv_dir / csv_file
                table_name = os.path.splitext(csv_file)[0]
                table_name = tname(clean_name(table_name))

                table = self.create_table_from_csv(file_path, table_name)

        db.update_metadata()
        self.update_admin("full")

        print("Ingested all CSV files and created tables.")



