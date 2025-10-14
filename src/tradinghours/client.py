import datetime, json, shutil, tempfile, zipfile, time, os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from typing import Tuple, Optional

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


def extract_zip_to_root(zip_path: Path) -> None:
    """Extract zip file to ROOT directory, clearing it first."""
    # Clear out the directory to make sure no old csv files
    # are present if the access level is reduced
    for path in os.listdir(ROOT):
        path = ROOT / path
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    
    # Extract zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(ROOT)


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


def download() -> Tuple[Optional[str]]:
    """
    Downloads zip file from data source and unzips it into the
    folder set in main_config.internal.remote_dir.
    
    Returns:
        Tuple of (version_identifier) for change tracking
    """
    from .sources import get_data_source
    
    try:
        # Get configured data source
        data_source = get_data_source()
        source_url = main_config.get("data", "source", fallback="")
        if not source_url:
            source_url = f"{BASE_URL}download"
        
        with timed_action("Downloading") as (change_message, start_time):
            # Download the zip file
            zip_path, version_identifier = data_source.download(ROOT)
            
            # Extract it
            extract_zip_to_root(zip_path)
            
            # Clean up temp file
            try:
                os.unlink(zip_path)
            except:
                pass

        download_covered_markets()
        download_covered_currencies()
        
        return version_identifier

    except TokenError:
        raise
    except Exception as e:
        raise

    