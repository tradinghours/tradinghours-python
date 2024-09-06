from typing import List

from .models.base import BaseModel
from .store import db

class Currency(BaseModel):

    @classmethod
    def list_all(cls) -> List["Currency"]:
        table = db.table("currencies")
        with db.session() as s:
            return [cls(
                {col:v for col, v in zip(table.c.keys(), r)}
            ) for r in s.query(table)]

    @classmethod
    def get(cls, code: str, catalog=None) -> "Currency":
        catalog = cls.get_catalog(catalog)
        return catalog.get(cls, code)
