import datetime as dt
from zoneinfo import ZoneInfo


def fromiso(iso: str, tz: str) -> dt.datetime:
    d = dt.datetime.fromisoformat(iso)
    return d.replace(tzinfo=ZoneInfo(tz))
