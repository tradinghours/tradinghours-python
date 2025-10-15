from itertools import groupby
import os, csv, json, codecs
import calendar
from collections import namedtuple
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
from .client import get_data_source
from .util import get_th_cache, set_th_cache, clean_name, timed_action
from .exceptions import DBError, NoAccess

DEFAULT_DB_PREFIX = "tradinghours_" # used for timestamped SQLite databases

# Helper functions for timestamped SQLite databases
def _is_default_store() -> bool:
    """Check if the database URL is the default SQLite database."""
    return True  # Always use default store (SQLite)

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
    _th_cache = get_th_cache()
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

    def __init__(self):
        latest_db_path = _find_latest_timestamped_db()
        self.db_url = f"sqlite:///{latest_db_path}"
        self._set_engine()
        
    def _set_engine(self):
        self.engine = create_engine(str(self.db_url))
        self.metadata = MetaData()
        try:
            self.update_metadata()
        except Exception:
            self._failed_to_access = True

        self.Session = sessionmaker(bind=self.engine)
        self._access_level = None

    def _switch_to_latest_db(self):
        """Assumes that the database is the default store."""
        latest_db_path = _find_latest_timestamped_db()
        new_db_url = f"sqlite:///{latest_db_path}"
        if new_db_url != self.db_url:
            self.db_url = new_db_url
            if hasattr(self, "_session"):
                self._session.close()
                delattr(self, "_session")
            self._set_engine()

        self.update_metadata()            
        self.cache_set()

    def switch_to_latest_db(self):
        self._switch_to_latest_db()


    def table(self, table_name: str) -> Table:
        try:
            return self.metadata.tables[table_name]
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

        if "admin" not in self.metadata.tables:
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

    def get_local_data_info(self):
        # admin table is not present when `tradinghours import`
        # is run for the first time on a given database
        if "admin" not in self.metadata.tables:
            return
        if "version_identifier" not in self.metadata.tables["admin"].columns:
            # this is to migrate to new set up with version_identifier column
            return

        table = self.table("admin")
        with self.session() as s:
            result = s.query(
                table.c["download_timestamp"],
                table.c["version_identifier"]
            ).order_by(
                    table.c["id"].desc()
            ).limit(1).first()
            if result:
                LocalDataInfo = namedtuple("LocalDataInfo", ["download_timestamp", "version_identifier"])
                return LocalDataInfo(
                    result.download_timestamp.replace(tzinfo=dt.timezone.utc),
                    result.version_identifier
                )
    
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
        """Check if data needs to be downloaded using version-based change detection."""        
        try:
            # Get the data source and check for changes
            data_source = get_data_source()
            local_data_info = self.get_local_data_info()
            stored_version = local_data_info.version_identifier if local_data_info else None
            new_version = data_source.check_for_changes(stored_version)
            return new_version
        except Exception as e:
            # If check fails, assume needs download
            print(f"Warning: Version check failed: {e}")
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

    def get_market_first_last_available_date(self) -> dict[str, list[str]]:
        table = db.table("holidays")
        result = self.query(
            table.c.fin_id,
            func.min(table.c.date).label('first_date'),
            func.max(table.c.date).label('last_date')
        ).group_by(table.c.fin_id).all()
        
        output = {}
        for row in result:
            last_date = row.last_date
            _, num_days_in_month = calendar.monthrange(last_date.year, last_date.month)
            last_date_adjusted = last_date.replace(day=num_days_in_month)
            
            output[row.fin_id] = [
                row.first_date.replace(day=1).isoformat(),
                last_date_adjusted.isoformat()
            ]
        
        return output

    def cache_get(self, value, fin_id):
        return self._th_cache.get(value, {}).get(fin_id, [])

    @classmethod
    def cache_set(cls, cache=None):
        if cache is None:
            first_last = cls.main_instance.get_market_first_last_available_date()
            cache = {
                "Market.first_last_available_date": first_last
            }
        cls._th_cache = cache
        set_th_cache(cls._th_cache)
        
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
        table_name = "admin"
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
        """Drops all tables from the database."""
        # Iterate over all tables in the metadata
        for table_name in self.db.metadata.tables:
            table = self.db.metadata.tables[table_name]
            table.drop(self.db.engine)

        # Clear the metadata cache after dropping tables
        self.db.update_metadata()

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

    def create_admin(self, access_level, last_9_records, version_identifier):
        """
        version_identifier could be ETag or mtime, depending on the data source.
        """
        table = Table(
            "admin",
            self.db.metadata,
            Column('id', Integer, primary_key=True),
            Column('access_level', String(255), nullable=False),
            Column('download_timestamp', DateTime, nullable=False),
            Column('version_identifier', String(255), nullable=True),
        )
        table.create(self.db.engine)
        if last_9_records:
            try:
                self.db.execute(table.insert(), last_9_records)
            except:
                pass

        self.db.execute(
            table.insert().values(
                access_level=access_level.value,
                download_timestamp=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
                version_identifier=version_identifier,
            )
        )
        self.db.update_metadata()

    def _finalize_db_setup(self):
        """Finalize the timestamped database setup and cleanup old databases."""   
        if _is_default_store():
            db._switch_to_latest_db()
            _cleanup_old_timestamped_dbs()
        else:
            db.cache_set({})


    def _ingest_all(self, change_message, version_identifier):
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
                table_name = clean_name(table_name)
                change_message(f"  {table_name}")
                self.create_table_from_csv(file_path, table_name)

        for json_file in ("covered_markets", "covered_currencies"):
            table_name = json_file
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

        self.create_admin(access_level, last_9_admin_records, version_identifier)
        
        self._finalize_db_setup()


    def ingest_all(self, version_identifier) -> bool:       
        # Create a new timestamped database for this import
        new_db_path = _create_timestamped_db_path()
        self.db = _DB()
        self.db.db_url = f"sqlite:///{new_db_path}"
        self.db._set_engine()

        with timed_action("Ingesting") as (change_message, start_time):
            self._ingest_all(change_message, version_identifier)
        
        return True




"""
full = all

only_holidays = no schedules
 
no_currencies = schedules but no currencies
"""

