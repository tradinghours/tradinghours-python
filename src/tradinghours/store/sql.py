from typing import Iterator

from sqlalchemy import (
    Column,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
)

from tradinghours.store.base import Cluster, Collection, Registry


class SqlCluster(Cluster):
    """Manages one page in a SQL database table"""

    DEFAULT_CACHE_SIZE = 500

    def __init__(self, engine, table, slug, cache_size=None):
        self._engine = engine
        self._table = table
        self._slug = slug
        self._cached = []
        self._cache_size = cache_size or self.DEFAULT_CACHE_SIZE

    def truncate(self):
        with self._engine.connect() as connection:
            connection.execute(f"DELETE FROM {self._table.name}")

    def append(self, key, data):
        # TODO: reuse FileCluster.append with fields set on flush
        self._cached.append({"slug": self._slug, "key": key, "data": data})
        if len(self._cached) >= self._cache_size:
            self.flush()

    def flush(self):
        with self._engine.connect() as connection:
            with connection.begin() as transaction:
                for record in self._cached:
                    connection.execute(self._table.insert().values(record))
                transaction.commit()
        self._cached = []

    def load_all(self):
        with self._engine.connect() as connection:
            select_query = self._table.select()
            result = connection.execute(select_query)
            return result.fetchall()


class SqlClusterRegistry(Registry[SqlCluster]):
    """Holds a series of SQL clusters"""

    def __init__(self, engine, table):
        self._engine = engine
        self._table = table

    def create(self, slug: str) -> SqlCluster:
        return SqlCluster(self._engine, self._table, slug)


class SqlCollection(Collection):
    def __init__(self, engine: Engine, table: Table):
        self._engine = engine
        self._table = table
        self._clusters = SqlClusterRegistry(self._engine, self._table)

    @property
    def clusters(self) -> SqlClusterRegistry:
        return self._clusters

    def touch(self):
        self._table.create(self._engine, checkfirst=True)


class SqlCollectionRegistry(Registry[SqlCollection]):
    def __init__(self, db_url: str):
        self._db_url = db_url
        self._engine = create_engine(self._db_url)
        self._metadata = MetaData()
        super().__init__()

    def create(self, slug: str) -> SqlCollection:
        table_name = "thstore_" + slug.replace("-", "_")
        table = Table(
            table_name,
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("slug", String),
            Column("key", String),
            Column("data", String),
        )
        collection = SqlCollection(self._engine, table)
        collection.touch()
        return collection

    def discover(self) -> Iterator[str]:
        inspector = inspect(self._engine)
        all_names = inspector.get_table_names()
        for table_name in all_names:
            if table_name.startswith("thstore_"):
                yield table_name
