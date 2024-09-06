from typing import Dict
from pprint import pprint


class BaseModel:
    def __init__(self, data):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict:
        return self._data.copy()

    def pprint(self):
        pprint(self.to_dict(), sort_dicts=False)

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self._data!r})"
