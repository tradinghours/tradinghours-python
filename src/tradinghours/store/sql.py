from typing import Dict, Iterator, Tuple

from ..exceptions import MissingSqlAlchemyError

try:
    from sqlalchemy import (
        JSON,
        Column,
        Engine,
        Integer,
        MetaData,
        String,
        Table,
        create_engine,
        inspect,
    )
except ImportError:
    raise MissingSqlAlchemyError("SQLAlchemy not installed")


from tradinghours.store.base import Cluster, Collection, Registry
from tradinghours.util import get_csv_from_tuple, get_tuple_from_csv

TABLE_NAME_PREFIX = "thstore_"


class SqlCluster(Cluster):
    """Manages one page in a SQL database table"""

    DEFAULT_CACHE_SIZE = 500

    def __init__(self, engine: Engine, table: Table, slug: str, cache_size=None):
        self._engine = engine
        self._table = table
        self._slug = slug
        self._cached = []
        self._cache_size = cache_size or self.DEFAULT_CACHE_SIZE

    def truncate(self):
        with self._engine.connect() as connection:
            connection.execute(f"DELETE FROM {self._table.name}")

    def flush(self):
        with self._engine.connect() as connection:
            with connection.begin() as transaction:
                for key, data in self._cached:
                    data_csv = get_csv_from_tuple(data)
                    db_record = {"slug": self._slug, "key": key, "data": data_csv}
                    connection.execute(self._table.insert().values(db_record))
                transaction.commit()
        self._cached = []

    def load_all(self) -> Dict[str, Tuple]:
        keyed_items = {}
        with self._engine.connect() as connection:
            select_query = (
                self._table.select()
                .add_columns(self._table.c.key, self._table.c.data)
                .where(self._table.c.slug == self._slug)
            )
            result = connection.execute(select_query)
            for row in result:
                key = row.key or str(row.id)
                data = get_tuple_from_csv(row.data)
                keyed_items[key] = data
        return keyed_items


class SqlClusterRegistry(Registry[SqlCluster]):
    """Holds a series of SQL clusters"""

    def __init__(self, engine: Engine, table: Table):
        self._engine = engine
        self._table = table
        super().__init__()

    def create(self, slug: str) -> SqlCluster:
        return SqlCluster(self._engine, self._table, slug)

    def discover(self) -> Iterator[str]:
        with self._engine.connect() as connection:
            select_query = (
                self._table.select().add_columns(self._table.c.slug).distinct()
            )
            result = connection.execute(select_query)
            for row in result:
                yield row.slug


class SqlCollection(Collection):
    def __init__(self, engine: Engine, table: Table):
        self._engine = engine
        self._table = table
        self.touch()
        self._clusters = SqlClusterRegistry(self._engine, self._table)

    @property
    def clusters(self) -> SqlClusterRegistry:
        return self._clusters

    def touch(self):
        self._table.create(self._engine, checkfirst=True)

    def clear(self):
        for current in self._clusters:
            current.truncate()
        self._clusters = SqlClusterRegistry(self._engine, self._table)


class SqlCollectionRegistry(Registry[SqlCollection]):
    def __init__(self, db_url: str):
        self._db_url = db_url
        self._engine = create_engine(self._db_url)
        self._metadata = MetaData()
        super().__init__()

    def create(self, slug: str) -> SqlCollection:
        table_name = TABLE_NAME_PREFIX + slug.replace("-", "_")
        table = Table(
            table_name,
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("slug", String),
            Column("key", String),
            Column("data", JSON),
        )
        collection = SqlCollection(self._engine, table)
        collection.touch()
        return collection

    def discover(self) -> Iterator[str]:
        inspector = inspect(self._engine)
        all_names = inspector.get_table_names()
        for table_name in all_names:
            if table_name.startswith(TABLE_NAME_PREFIX):
                yield table_name[len(TABLE_NAME_PREFIX) :]
