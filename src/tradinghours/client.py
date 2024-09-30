import datetime, json, shutil, tempfile, zipfile, time
from contextlib import contextmanager
from threading import Thread, Event
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from http.client import HTTPResponse

from .config import main_config
from .exceptions import ClientError, TokenError

TOKEN = main_config.get("api", "token")
BASE_URL = main_config.get("api", "base_url")
ROOT = Path(main_config.get("data", "remote_dir"))
ROOT.mkdir(parents=True, exist_ok=True)


@contextmanager
def timed_action(message: str):
    start = time.time()
    print(f"{message}...", end="", flush=True)

    done = False
    change_message_event = Event()
    current_message = [message]  # Using a mutable object to allow modification inside the thread

    def print_dots():
        changed_already = False
        while not done:
            if change_message_event.is_set() and not changed_already:
                changed_already = True
                # Move to the next line and print the new message
                print(f"\n{current_message[0]}...", end="", flush=True)
                change_message_event.clear()

            print(".", end="", flush=True)
            time.sleep(0.5 if not changed_already else 2)

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
    print(f" ({elapsed:.3f}s)")


def get_response(path):
    url = urljoin(BASE_URL, path)
    request = Request(url)
    request.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        response = urlopen(request)
    except HTTPError as error:
        if error.code == 401:
            raise TokenError("Token is missing or invalid")
        raise ClientError("Error getting server response", inner=error)

    return response


def download_zip_file(path="download"):
    response = get_response(path)
    if response.status == 200:
        with tempfile.NamedTemporaryFile() as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()
            temp_file.seek(0)
            with zipfile.ZipFile(temp_file, "r") as zip_ref:
                zip_ref.extractall(ROOT)
        return True
    elif response.status == 202:
        return False

    raise ClientError("Error getting server response")


def download_covered_markets():
    response = get_response("markets?group=all")
    markets = json.load(response).get("data", [])
    with open(ROOT / "covered_markets.json", "w") as covered_markets:
        json.dump(markets, covered_markets)


def download_covered_currencies():
    response = get_response("currencies")
    markets = json.load(response).get("data", [])
    with open(ROOT / "covered_currencies.json", "w") as covered_currencies:
        json.dump(markets, covered_currencies)


def download():
    """
    Downloads zip file from tradinghours and unzips it into the
    folder set in main_config.data.remote_dir
    """
    try:
        with timed_action("Downloading") as (change_message, start_time):
            waited = False
            while True:
                downloaded = download_zip_file()
                if downloaded:
                    break
                if (time.time() - start_time) > 120:
                    raise ClientError("Failed downloading data, please try again.")

                change_message("Generating (~ 1min)")
                time.sleep(5 if waited else 30)
                waited = True

        download_covered_markets()
        download_covered_currencies()

    except TokenError:
        raise
    # TODO: think about cleaner error handling (e.g: not a zipfile)
    except Exception as e:
        raise


def get_remote_timestamp() -> datetime.datetime:
    response = get_response("last-updated")
    data = json.load(response)
    last_updated = data["last_updated"]
    timestamp = datetime.datetime.fromisoformat(last_updated)
    return timestamp

