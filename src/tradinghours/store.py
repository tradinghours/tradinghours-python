import os, csv, json, codecs
import datetime as dt
from pathlib import Path
from sqlalchemy import (
    create_engine,
    MetaData,
    func,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    Time,
    Date,
    Boolean,
    Text
)
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Union
import functools
from enum import Enum

from .config import main_config, default_settings
from .client import get_remote_timestamp as client_get_remote_timestamp
from .util import tprefix, tname, clean_name, timed_action
from .exceptions import DBError, NoAccess

DEFAULT_DB_PREFIX = "tradinghours_"

# Helper functions for timestamped SQLite databases
def _is_default_store() -> bool:
    """Check if the database URL is the default SQLite database."""
    return not main_config.get("package-mode", "db_url")

def _find_timestamped_dbs() -> list[Path]:
    """Find all timestamped database files."""
    directory = Path(main_config.get("internal", "store_dir"))
    pattern = f"{DEFAULT_DB_PREFIX}*.db"
    return list(directory.glob(pattern))

def _find_latest_timestamped_db() -> Path:
    """Find the latest timestamped database file, or return base_path if none exist."""
    timestamped_files = _find_timestamped_dbs()
    if not timestamped_files:
        return _create_timestamped_db_path()
    timestamped_files.sort(key=lambda p: p.stem.split('_')[-2:])  # Sort by date_time parts
    return timestamped_files[-1]

def _create_timestamped_db_path() -> Path:
    """Create a new timestamped database path."""
    directory = Path(main_config.get("internal", "store_dir"))
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    return directory / f"{DEFAULT_DB_PREFIX}{timestamp}.db"

def _cleanup_old_timestamped_dbs() -> None:
    """Remove old timestamped databases, keeping only the latest 1."""
    timestamped_files = _find_timestamped_dbs()
    timestamped_files.sort(key=lambda p: p.stem.split('_')[-2:])
    files_to_remove = timestamped_files[:-1]
    for file_path in files_to_remove:
        try:
            file_path.unlink()
        except OSError:
            pass  # Ignore errors during cleanup

class AccessLevel(Enum):
    full = "full"
    no_currencies = "no_currencies"
    only_holidays = "only_holidays"
    no_access = None

class _DB:
    main_instance = None
    _types = {
        "date": (Date, dt.date.fromisoformat),
        "observed": (Boolean, lambda v: v == "OBS"),
        "start": (Time, dt.time.fromisoformat),
        "end": (Time, dt.time.fromisoformat),
        "offset_days": (Integer, int),
        "duration": (Integer, int),
        "min_start": (Time, dt.time.fromisoformat),
        "max_start": (Time, dt.time.fromisoformat),
        "min_end": (Time, dt.time.fromisoformat),
        "max_end": (Time, dt.time.fromisoformat),
        "in_force_start_date": (Date, dt.date.fromisoformat),
        "in_force_end_date": (Date, dt.date.fromisoformat),
        "year": (Integer, int),
        # Everything else is Text
    }
    _default_type = (Text, str)
    _access = {
        "Currency.list_all" : {AccessLevel.full},
        "Currency.get": {AccessLevel.full},
        "Currency.is_covered": {AccessLevel.full},
        "Market.list_schedules": {AccessLevel.full, AccessLevel.no_currencies},
        "Market.generate_phases": {AccessLevel.full, AccessLevel.no_currencies},
        "Market.status": {AccessLevel.full, AccessLevel.no_currencies}
    }
    _no_model_access = {
        AccessLevel.full: set(),
        AccessLevel.no_currencies: {"currencies", "currency_holidays"},
        AccessLevel.only_holidays: {"currencies", "currency_holidays", "phases", "schedules", "season_definitions"}
    }

    @classmethod
    def set_no_unicode(cls):
        """
        MySQL databases may not be able to handle the full unicode set by default. So if a
        mysql db is used and the ingestion fails, it is attempted again with the following
        conversion, which replaces unicode characters with '?'.
        """
        cls._default_type = (
            Text,
            lambda s: str(s).encode("ascii", "replace").decode("ascii")
        )

    @classmethod
    def get_type(cls, col_name):
        return cls._types.get(col_name, cls._default_type)[0]

    @classmethod
    def clean(cls, col_name: str, value: Union[bool, str, None]) -> Union[bool, str, None]:
        """
        Used to map values from the csv files to what they should be in the database
         For observed columns 'OBS' is True, anything else is False
         For other columns, empty strings should be converted to None
        """
        converter = cls._types.get(col_name, cls._default_type)[1]
        if col_name == "observed":
            return converter(value)

        return converter(value) if value else None

    def __init__(self, db_url=None):
        if db_url is not None:
            self.db_url = db_url

        elif _is_default_store():
            latest_db_path = _find_latest_timestamped_db()
            self.db_url = f"sqlite:///{latest_db_path}"
        else:
            self.db_url = main_config.get("package-mode", "db_url")

        self._set_engine()
        
    def _set_engine(self):
        try:
            self.engine = create_engine(str(self.db_url))
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "You seem to be missing the required dependencies to interact with your chosen database. "
                "Please run `pip install tradinghours[mysql]` or `pip install tradinghours[postgres]` if "
                "you are trying to access mysql or postgres, respectively. Consult the docs for more information."
            ) from e

        self.metadata = MetaData()
        try:
            self.update_metadata()
        except Exception:
            self._failed_to_access = True

        self.Session = sessionmaker(bind=self.engine)
        self._access_level = None

    def switch_to_latest_db(self):
        if _is_default_store():
            latest_db_path = _find_latest_timestamped_db()
            new_db_url = f"sqlite:///{latest_db_path}"
            if new_db_url != self.db_url:
                self.db_url = new_db_url
                if hasattr(self, "_session"):
                    self._session.close()
                    delattr(self, "_session")
                self._set_engine()

    def table(self, table_name: str) -> Table:
        try:
            return self.metadata.tables[tname(table_name)]
        except KeyError:
            # using self._access_level instead of property to avoid an infinite recursion
            # when running on a new database without an access_level. If ._access_level is None,
            # it would check if table_name is in an empty set, which would make it raise a KeyError,
            # which is handled properly in .access_level property.
            if self._access_level == AccessLevel.no_access:
                raise DBError(f"{table_name} could not be found. Are you sure you ran `tradinghours import`?")

            if table_name in self._no_model_access.get(self._access_level, set()):
                raise NoAccess(
                    f"\nIf you are sure you ran `tradinghours import`, {table_name} is not available on your current plan."
                    f"\nPlease learn more or contact sales at https://www.tradinghours.com/data"
                )
            raise

    def ready(self) -> None:
        if getattr(self, "_failed_to_access", True):
            raise DBError("Could not access database")

        if tname("admin") not in self.metadata.tables:
            raise DBError("Database not prepared. Did you run `tradinghours import`?")

    def reset_session(self):
        if hasattr(self, "_session"):
           self._session.rollback()
           self._session.close()

        self._session = self.Session()

    @contextmanager
    def session(self):
        if hasattr(self, "_session"):
            s = self._session
        else:
            s = self._session = self.Session()
        yield s

    def execute(self, *query):
        with self.session() as s:
            result = s.execute(*query)
            s.commit()
            return result

    def query(self, *query):
        with self.session() as s:
            return s.query(*query)

    def get_local_timestamp(self):
        # admin table is not present when `tradinghours import`
        # is run for the first time on a given database
        if tname("admin") not in self.metadata.tables:
            return

        table = self.table("admin")
        with self.session() as s:
            result = s.query(
                table.c["download_timestamp"]).order_by(
                    table.c["id"].desc()
            ).limit(1).scalar()
            if result:
                return result.replace(tzinfo=dt.timezone.utc)

    @property
    def access_level(self) -> AccessLevel:
        if self._access_level is None:
            try:
                table = self.table("admin")
            except KeyError:
                # This should only be the case when ingesting into a completely new
                # database, that doesn't have an admin table yet.
                level = None
            else:
                level = self.query(table.c.access_level).order_by(
                    table.c.id.desc()
                ).limit(1).scalar()
            self._access_level = AccessLevel(level)

        return self._access_level

    @classmethod
    def check_access(cls, method):
        """
        Used as a decorator of Currency and Market methods,
         to check whether the user has access to the data requested.
        """
        method_name = method.__qualname__
        not_has_access = db.access_level not in cls._access[method_name]

        @functools.wraps(method)
        def new_method(*args, **kwargs):
            if not_has_access:
                raise NoAccess(f"\n\n{method_name} is supported but not available on your current plan."
                               f"\nPlease learn more or contact sales at https://www.tradinghours.com/data")
            return method(*args, **kwargs)

        return new_method

    def needs_download(self):
        if local := self.get_local_timestamp():
            remote_timestamp = client_get_remote_timestamp()
            return remote_timestamp > local
        return True

    def update_metadata(self):
        self.metadata.clear()
        self.metadata.reflect(bind=self.engine)
        self._failed_to_access = False

    def get_num_covered(self) -> tuple[int, int]:
        table = db.table("covered_markets")
        num_markets = self.query(func.count()).select_from(table).scalar()
        table = db.table("covered_currencies")
        num_currencies = self.query(func.count()).select_from(table).scalar()
        return num_markets, num_currencies

    def get_num_permanently_closed(self) -> int:
        table = db.table("markets")
        num = self.query(func.count()).filter(
            table.c.permanently_closed.isnot(None)
        ).scalar()
        return num

########################################################
# Singleton db instance used across the entire project #
########################################################
db = _DB()
_DB.main_instance = db


# noinspection PyMethodMayBeStatic
class Writer:

    def __init__(self):
        self.remote = Path(main_config.get("internal", "remote_dir"))

    def prepare_ingestion(self):
        """Preserves the last 9 records from the thstore_admin table,
        drops the table, recreates it, and re-inserts the 9 records."""
        table_name = tname("admin")
        last_9_records = []
        if table_name not in self.db.metadata.tables:
            return last_9_records

        table = self.db.metadata.tables[table_name]
        columns_to_select = [col for col in table.c.values() if col.name != 'id']
        result = self.db.execute(
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
        table.drop(self.db.engine)
        self.db.update_metadata()

        return last_9_records

    def drop_th_tables(self):
        """Drops all tables from the database that start with 'thstore_'."""
        # Iterate over all tables in the metadata
        for table_name in self.db.metadata.tables:
            if table_name.startswith(tprefix):
                table = self.db.metadata.tables[table_name]
                table.drop(self.db.engine)

        # Clear the metadata cache after dropping tables
        self.db.update_metadata()
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
                self.db.metadata,
                Column('id', Integer, primary_key=True),
                *(Column(col_name, self.db.get_type(col_name)) for col_name in columns)
            )
            batch = []
            for i, row in enumerate(reader):
                values = {col_name: self.db.clean(col_name, value) for col_name, value in zip(columns, row)}
                batch.append(values)

        table.create(self.db.engine)
        self.db.execute(table.insert(), batch)

    def create_table_from_json(self, file_path, table_name):
        """
        This method takes a filepath to a json file that should hold a list of dictionaries.
         It is probably redundant, but it makes sure that the table created is flexible in regard to
         the content of the dictionaries by following these steps:

        # find all keys that exist
        # filter out keys that don't exist in every dictionary
        # clean these keys using clean_name
        # create a table with the cleaned keys
        # insert a batch of fields that exist in every dictionary
        """
        with open(file_path, "r") as data:
            data = json.load(data)

        keys = {}
        len_data = 0
        for dct in data:
            len_data += 1
            for k in dct:
                keys[k] = keys.setdefault(k, 0) + 1

        columns = [(k, clean_name(k)) for k, n in keys.items() if n == len_data]
        table = Table(
            table_name,
            self.db.metadata,
            Column('id', Integer, primary_key=True),
            *(Column(col_name, self.db.get_type(col_name)) for k, col_name in columns)
        )
        batch = []
        for dct in data:
            batch.append({clean_k: self.db.clean(clean_k, dct.get(k, "")) for k, clean_k in columns})

        table.create(self.db.engine)
        self.db.execute(table.insert(), batch)

    def create_admin(self, access_level, last_9_records):
        version_file = self.remote / "VERSION.txt"
        timestamp_format = "Generated at %a, %d %b %Y %H:%M:%S %z"
        content = version_file.read_text()
        line = content.splitlines()[0]
        data_timestamp = dt.datetime.strptime(line, timestamp_format)

        table = Table(
            tname("admin"),
            self.db.metadata,
            Column('id', Integer, primary_key=True),
            Column('data_timestamp', DateTime, nullable=False),
            Column('access_level', String(255), nullable=False),
            Column('download_timestamp', DateTime, nullable=False),
        )
        table.create(self.db.engine)
        if last_9_records:
            self.db.execute(table.insert(), last_9_records)

        self.db.execute(
            table.insert().values(
                data_timestamp=data_timestamp,
                access_level=access_level.value,
                download_timestamp=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            )
        )
        self.db.update_metadata()

    def _finalize_timestamped_db(self):
        """Finalize the timestamped database setup and cleanup old databases."""        
        if _is_default_store():
            # make the main db instance point to the latest timestamped database
            db.switch_to_latest_db()
            db.update_metadata()            
            _cleanup_old_timestamped_dbs()


    def _ingest_all(self, change_message):
        """Iterates over CSV files in the remote directory and ingests them."""
        # Set up timestamped database if needed        
        self.db.reset_session()
        last_9_admin_records = self.prepare_ingestion()
        self.drop_th_tables()

        csv_dir = self.remote / "csv"
        # Iterate over all CSV files in the directory
        downloaded_csvs = os.listdir(csv_dir)

        for csv_file in downloaded_csvs:
            if csv_file.endswith('.csv'):
                file_path = csv_dir / csv_file
                table_name = os.path.splitext(csv_file)[0]
                table_name = tname(clean_name(table_name))
                change_message(f"  {table_name}")
                self.create_table_from_csv(file_path, table_name)

        for json_file in ("covered_markets", "covered_currencies"):
            table_name = tname(json_file)
            change_message(f"  {table_name}")
            self.create_table_from_json(
                self.remote / f"{json_file}.json",
                table_name
            )

        self.db.update_metadata()

        if "schedules.csv" not in downloaded_csvs:
            access_level = AccessLevel.only_holidays
        elif "currencies.csv" not in downloaded_csvs:
            access_level = AccessLevel.no_currencies
        else:
            access_level = AccessLevel.full

        self.create_admin(access_level, last_9_admin_records)
        
        # Finalize the timestamped database setup
        self._finalize_timestamped_db()
        

    def ingest_all(self) -> bool:       
        self.db = db
        if _is_default_store():
            self.db = _DB(db_url="sqlite:///" + str(_create_timestamped_db_path()))

        with timed_action("Ingesting") as (change_message, start_time):
            try:
                self._ingest_all(change_message)
                return True
            except Exception as e:
                if self.db.engine.dialect.name != "mysql" or "Incorrect string value" not in str(e):
                    raise

        # Deal with the problem that MySQL may not be able to
        # handle the full unicode set and then try again
        print("\nHandling unicode problem, warning will follow")
        self.db.set_no_unicode()
        with timed_action("Ingesting") as (change_message, start_time):
            self._ingest_all(change_message)
        return False




"""
full = all

only_holidays = no schedules
 
no_currencies = schedules but no currencies
"""

