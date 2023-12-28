from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from tradinghours.store.base import Cluster, Collection


class SqlCluster(Cluster):
    """Manages one page in a SQL database table"""

    DEFAULT_CACHE_SIZE = 500

    def __init__(self, db_url, table_name, cache_size=None):
        self._db_url = db_url
        self._table_name = table_name
        self._cached = []
        self._cache_size = cache_size or self.DEFAULT_CACHE_SIZE

        self.engine = create_engine(self._db_url)
        self.metadata = MetaData()

        self.cluster_table = Table(
            self._table_name,
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("key", String),
            Column("data", String),
        )
        self.metadata.create_all(self.engine)

    def truncate(self):
        with self.engine.connect() as connection:
            connection.execute(f"DELETE FROM {self._table_name}")

    def append(self, key, data):
        self._cached.append({"key": key, "data": data})
        if len(self._cached) >= self._cache_size:
            self.flush()

    def flush(self):
        with self.engine.connect() as connection:
            with connection.begin() as transaction:
                for record in self._cached:
                    connection.execute(self.cluster_table.insert().values(record))
                transaction.commit()
        self._cached = []

    def load_all(self):
        with self.engine.connect() as connection:
            select_query = self.cluster_table.select()
            result = connection.execute(select_query)
            return result.fetchall()


class SqlCollection(Collection):
    pass
