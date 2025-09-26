import datetime, json, shutil, tempfile, zipfile, time, os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .config import main_config
from .util import timed_action
from .exceptions import ClientError, TokenError, FileNotFoundError

TOKEN = main_config.get("auth", "token")
BASE_URL = main_config.get("internal", "base_url")
ROOT = Path(main_config.get("internal", "remote_dir"))
ROOT.mkdir(parents=True, exist_ok=True)


def get_response(path):
    url = urljoin(BASE_URL, path)
    request = Request(url)
    request.add_header("Authorization", f"Bearer {TOKEN}")
    request.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    try:
        response = urlopen(request)
    except HTTPError as error:
        if error.code == 401:
            raise TokenError("Token is missing or invalid")
        if error.code == 404:
            raise FileNotFoundError("Error getting server response", inner=error)
        raise ClientError("Error getting server response", inner=error)

    return response


def download_zip_file(path="download"):
    response = get_response(path)
    if response.status == 200:
        with tempfile.NamedTemporaryFile() as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()
            temp_file.seek(0)

            # clear out the directory to make sure no old csv files
            # are present if the access level is reduced
            for path in os.listdir(ROOT):
                path = ROOT / path
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

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
    folder set in main_config.internal.remote_dir
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

