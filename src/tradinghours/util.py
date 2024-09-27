import csv
import json
import re
from io import StringIO
from typing import Dict

from zoneinfo import TZPATH
import importlib.metadata as metadata
import requests, warnings

from .exceptions import MissingTzdata
from .config import main_config

tprefix = main_config.get("data", "table_prefix")


def tname(table_name):
    return f"{tprefix}{table_name}"

def clean_name(name):
    name = name.lower().replace('"', '').replace("finid", "fin_id")
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


WEEKDAYS = {
    d: i for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
}

def weekdays_match(weekday_set, weekday):
    for period_str in weekday_set.split(","):
        if "-" in period_str:
            day_range = [WEEKDAYS[x] for x in period_str.split("-")]
            if weekday in day_range:
                return True

            start_day, end_day = day_range
            day = start_day
            while day != end_day:
                if day == 6:
                    day = 0
                else:
                    day += 1
                if weekday == day:
                    return True

        elif weekday == WEEKDAYS[period_str]:
            return True

    return False


def _get_latest_tzdata_version():
    try:
        response = requests.get(f"https://pypi.org/pypi/tzdata/json")
    except requests.exceptions.RequestException:
        return None

    if response.status_code == 200:
        return response.json()["info"]["version"]


def check_if_tzdata_required_and_up_to_date():
    """
    required installed # check for version
    required notinstalled # raise error
    notrequired installed # doesn't matter
    notrequired notinstalled # doesn't matter
    [don't check]

    if required (no tzpath)
        get version
        if not version:
            raise Error # required notinstalled
        else:
            check version/give warning # required installed
    else (tzpath):

    """
    if not main_config.getboolean("control", "check_tzdata"):
        return False

    required = len(TZPATH) == 0
    if required:
        try:
            installed_version = metadata.version('tzdata')
        except metadata.PackageNotFoundError:
            raise MissingTzdata("\nYour environment does not provide timezone data and\n"
                                "you don't have tzdata installed, please run:\n"
                                " pip install tzdata") from None

        latest_version = _get_latest_tzdata_version()
        if latest_version is None:
            warnings.warn("Failed to get latest version of tzdata. "
                          "Check your internet connection or set "
                          "check_tzdata = False under [control] in tradinghours.ini")
            return None

        if installed_version < latest_version:
            warnings.warn(f"\nThe installed version of tzdata is {installed_version}\n"
                          f"The latest version of tzdata is    {latest_version}\n"
                          f"Please run: pip install tzdata --upgrade")
            return None

    return True