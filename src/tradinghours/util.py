import re, time, json, asyncio
from contextlib import contextmanager
from threading import Thread, Event
from pathlib import Path

from zoneinfo import TZPATH
import importlib.metadata as metadata
import requests, warnings

from .exceptions import MissingTzdata
from .config import main_config

@contextmanager
def timed_action(message: str):
    start = time.time()
    print(f"{message}...", end="", flush=True)

    done = False
    change_message_event = Event()
    current_message = [message]
    last_message = [message]

    def print_dots():
        last_check = time.time()
        while not done:
            if change_message_event.is_set() and current_message != last_message:
                # Move to the next line and print the new message
                print(f"\n{current_message[0]}...", end="", flush=True)
                last_message[0] = current_message[0]
                change_message_event.clear()

            if time.time() - last_check > 1:
                print(".", end="", flush=True)
                last_check = time.time()
            time.sleep(0.05)

    thread = Thread(target=print_dots)
    thread.daemon = True
    thread.start()

    # Function to change the message from within the main block
    def change_message(new_message):
        current_message[0] = new_message
        change_message_event.set()

    yield change_message, start

    elapsed = time.time() - start
    done = True
    thread.join()
    print(f" ({elapsed:.3f}s)", flush=True)


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
    if not main_config.getboolean("extra", "check_tzdata"):
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
                          "check_tzdata = False under [extra] in tradinghours.ini")
            return None

        if installed_version < latest_version:
            warnings.warn(f"\nThe installed version of tzdata is {installed_version}\n"
                          f"The latest version of tzdata is    {latest_version}\n"
                          f"Please run: pip install tzdata --upgrade")
            return None

    return True

async def auto_import_async(frequency_minutes: int):
    """Background task for periodic data imports."""
    while True:
        await asyncio.sleep(frequency_minutes * 60)
        try:
            needs_download = await asyncio.to_thread(db.needs_download)
            if needs_download:
                version_identifier = await asyncio.to_thread(data_download)
                await asyncio.to_thread(Writer().ingest_all, version_identifier)
        except Exception as e:
            logger.exception(f"Auto-import failed: {e}")
