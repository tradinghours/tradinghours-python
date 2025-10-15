import datetime, json, shutil, tempfile, zipfile, time, os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from typing import Tuple, Optional, Union

from . import __version__
from .config import main_config
from .util import timed_action
from .exceptions import ClientError, TokenError, FileNotFoundError, TradingHoursError, ConfigError

# Check for boto3 availability
try:
    import boto3
except ImportError:
    AWS_AVAILABLE = False
else:
    AWS_AVAILABLE = True

TOKEN = main_config.get("auth", "token")
REMOTE_DIR = Path(main_config.get("internal", "remote_dir"))
REMOTE_DIR.mkdir(parents=True, exist_ok=True)

class StripAuthOnS3Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Strip Authorization when redirecting to S3 (any domain, really)
        if urlparse(req.full_url).netloc != urlparse(newurl).netloc:
            headers = {h: v for h, v in headers.items() if h.lower() != "authorization"}
            return Request(newurl, headers=headers, method=req.get_method())
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class DataSource(ABC):
    @staticmethod
    def extract_zip_to_remote_dir(zip_path: Path) -> None:
        """Extract zip file to REMOTE_DIR directory, clearing it first."""
        # Clear out the directory to make sure no old csv files
        # are present if the access level is reduced
        for path in os.listdir(REMOTE_DIR):
            path = REMOTE_DIR / path
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        # Extract zip file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(REMOTE_DIR)

    @abstractmethod
    def check_for_changes(self, stored_version: Optional[str] = None) -> Optional[str]:
        pass
    @abstractmethod
    def get(self) -> Optional[str]:
        pass


class HTTPDataSource(DataSource):
    """Data source that downloads from HTTP/HTTPS URLs."""
    
    def __init__(self, url: str):
        self.opener = build_opener(StripAuthOnS3Redirect)
        self.url = url
        if "tradinghours.com" in url:
            self.token = main_config.get("auth", "token", fallback=None) 
            if not self.token:
                raise TokenError("Token is missing or invalid")

    def _make_request(self, method: str = "GET", if_none_match: Optional[str] = None) -> object:
        """Make an HTTP request with appropriate headers."""
        request = Request(self.url, method=method)
        print("making request", self.url, method)
        request.add_header("User-Agent", f"tradinghours-python/{__version__}")        
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        if if_none_match:
            request.add_header("If-None-Match", if_none_match)
        
        try:
            return self.opener.open(request)
        except HTTPError as error:
            if error.code == 304:
                # Not modified - this is actually expected for HEAD If-None-Match requests
                return False
            if error.code in (401, 403):
                raise TokenError("Token is missing or invalid")
            if error.code == 404:
                if method == "HEAD":
                    return False
                raise ClientError(f"Resource not found at {self.url}")
            raise ClientError(f"Error getting server response: {error}") from error
    
    def check_for_changes(self, stored_version: Optional[str] = None) -> Optional[str]:
        """Check for changes using ETag or Last-Modified header."""
        try:
            response = self._make_request(method="HEAD", if_none_match=stored_version)
            if response is False:
                return None
            
            etag = response.headers.get('ETag') or response.headers.get('etag')
            if etag:
                etag = etag.strip().strip('"')
                return etag if etag != stored_version else None
            
            last_modified = response.headers.get('Last-Modified') or response.headers.get('last-modified')
            if last_modified:
                return last_modified if last_modified != stored_version else None

        except Exception as e:
            return None
    
    def get(self) -> Optional[str]:
        """Download data file and extract it."""
        response = self._make_request(method="GET")
        # Get ETag or Last-Modified for tracking (making it support both for proprietary APIs)
        etag = response.headers.get('ETag') or response.headers.get('etag')
        if etag:
            version_identifier = etag.strip().strip('"')
        else:
            version_identifier = response.headers.get('Last-Modified') or response.headers.get('last-modified')
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()
            self.extract_zip_to_remote_dir(Path(temp_file.name))
        
        return version_identifier


class FileDataSource(DataSource):
    """Data source that reads from local filesystem."""
    
    def __init__(self, url: str):
        # Parse file:// URL to local path
        parsed = urlparse(url)
        # Handle both Unix and Windows paths
        path = unquote(parsed.path)
        
        # On Windows, file:///C:/path becomes /C:/path, need to remove leading /
        if os.name == 'nt' and path.startswith('/') and len(path) > 2 and path[2] == ':':
            path = path[1:]
        
        self.file_path = Path(path)
        if not self.file_path.exists():
            raise ClientError(f"File not found: {self.file_path}")
    
    def check_for_changes(self, stored_version: Optional[str] = None) -> Optional[str]:
        """Check for changes using file modification time."""
        try:
            mtime = os.path.getmtime(self.file_path)
            mtime_str = str(mtime)
            if mtime_str != stored_version:
                return mtime_str
        except Exception as e:
            return None
    
    def get(self) -> Optional[str]:
        """Copy file and return path with mtime."""
        mtime = os.path.getmtime(self.file_path)
        mtime_str = str(mtime)
        self.extract_zip_to_remote_dir(Path(self.file_path))
        return mtime_str


class S3DataSource(DataSource):
    """Data source that downloads from S3 (requires boto3)."""
    
    def __init__(self, url: str):
        if not AWS_AVAILABLE:
            raise TradingHoursError(
                "S3 data source requires boto3. Install with: pip install tradinghours[s3]"
            )
        
        parsed = urlparse(url)
        self.bucket = parsed.netloc
        self.key = parsed.path.lstrip('/')
        
        if not self.bucket or not self.key:
            raise TradingHoursError(
                f"Invalid S3 URL: {url}, please use the S3 URI in the format s3://bucket/key"
            )
        
        self.s3_client = boto3.client('s3')
    
    def check_for_changes(self, stored_version: Optional[str] = None) -> Optional[str]:
        """Check for changes using S3 ETag."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=self.key)
            etag = response.get('ETag', '').strip('"')
            if not stored_version:
                return etag
            if etag != stored_version.strip('"'):
                return etag
            
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] != '304':
                raise
        
    
    def get(self) -> Tuple[Path, Optional[str]]:
        """Download from S3 and return path with ETag.
        Gets ETag from the response of the download request, no extra HEAD needed.
        """
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_file:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self.key)
            shutil.copyfileobj(response['Body'], temp_file)
            temp_path = temp_file.name
            etag = response.get('ETag', '').strip('"')
            self.extract_zip_to_remote_dir(Path(temp_path))
            return etag



def get_data_source() -> Union[HTTPDataSource, FileDataSource, S3DataSource]:
    source_url = main_config.get("data", "source") # should be there by default
    if not source_url: # use default v4 API
        raise ConfigError("Config option [data].source is empty.")
    try:
        parsed = urlparse(source_url)
        scheme = parsed.scheme.lower()
    except Exception as e:
        scheme = None
    
    if scheme in ('http', 'https'):
        return HTTPDataSource(source_url)
    elif scheme == 'file':
        return FileDataSource(source_url)
    elif scheme == 's3':
        return S3DataSource(source_url)
    else:
        raise ConfigError(
            f"Unsupported data source or format: {source_url}. "
            f"Make sure source starts with one of the following: http://, https://, file://, or s3://"
        )


def data_download() -> Tuple[Optional[str]]:
    """
    Downloads zip file from data source and unzips it into the
    folder set in main_config.internal.remote_dir.
    
    Returns:
        Tuple of (version_identifier) for change tracking
    """
    # Get configured data source
    data_source = get_data_source()
    
    with timed_action("Downloading") as (change_message, start_time):
        # Download the zip file
        version_identifier = data_source.get()
        
    download_covered_markets()
    download_covered_currencies()
    
    return version_identifier

