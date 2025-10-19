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
from .exceptions import ClientError, TokenError, TradingHoursError, ConfigError, NoVersionIdentifierFoundError
from .store import db

# Check for boto3 availability
try:
    import boto3
except ImportError:
    AWS_AVAILABLE = False
else:
    AWS_AVAILABLE = True

TOKEN = main_config.get("data", "token")
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
    def __init__(self, url: str):
        self.source_url = url

    @staticmethod
    def extract_zip_to_remote_dir(zip_path: Path, delete: bool = True) -> None:
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

        if delete:
            os.remove(zip_path)


    def needs_download(self) -> bool:
        """Check if data needs to be downloaded using version-based change detection."""        
        try:
            local_data_info = db.get_local_data_info()
            local_version = local_data_info.version_identifier if local_data_info else None
            if local_version is None:
                return True

            remote_version = self.get_remote_version()
            if remote_version is None or remote_version != local_version:
                return True

            return False
        except Exception as e:
            return True

    def download(self) -> Optional[str]:
        with timed_action("Downloading") as (change_message, start_time):
            version_identifier = self.get()
        return version_identifier

    @abstractmethod
    def get_remote_version(self) -> Optional[str]:
        pass

    @abstractmethod
    def get(self) -> Optional[str]:
        pass


class HTTPDataSource(DataSource):
    """Data source that downloads from HTTP/HTTPS URLs."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.opener = build_opener(StripAuthOnS3Redirect)
        self.url = url
        if "tradinghours.com" in url:
            self.token = main_config.get("data", "token", fallback=None) 
            if not self.token:
                raise TokenError("Token is missing or invalid")

    def _make_request(self, method: str = "GET") -> object:
        """Make an HTTP request with appropriate headers."""
        request = Request(self.url, method=method)
        request.add_header("User-Agent", f"tradinghours-python/{__version__}")        
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            return self.opener.open(request)
        except HTTPError as error:
            if error.code in (401, 403):
                raise TokenError("Token is missing or invalid")
            raise ClientError(f"Error getting server response: {error}") from error
    
    def get_remote_version(self) -> Optional[str]:
        """Check for changes using ETag."""
        try:
            response = self._make_request(method="HEAD")
            etag = response.headers.get('ETag') or response.headers.get('etag')
            if etag:
                return etag.strip().strip('"')
        except Exception as e:
            return None
    
    def get(self) -> Optional[str]:
        """Download data file and extract it."""
        response = self._make_request(method="GET")
        etag = response.headers.get('ETag') or response.headers.get('etag')
        if etag:
            version_identifier = etag.strip().strip('"')
        else:
            version_identifier = None

        # Download to temporary file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()

        self.extract_zip_to_remote_dir(Path(temp_file.name), delete=True)
        
        return version_identifier


class FileDataSource(DataSource):
    """Data source that reads from local filesystem."""
    
    def __init__(self, url: str):
        super().__init__(url)
        path = url.split("file://")[1]
        path = unquote(path)
        self.file_path = Path(path)
        if not self.file_path.exists():
            raise ClientError(f"File not found: {self.file_path}")
    
    def get_remote_version(self) -> Optional[str]:
        """Check for changes using file modification time."""
        try:
            mtime = os.path.getmtime(self.file_path)
            if not mtime:
                return None
            return str(mtime)
        except Exception as e:
            return None
    
    def get(self) -> Optional[str]:
        """Copy file and return path with mtime."""
        self.extract_zip_to_remote_dir(Path(self.file_path), delete=False)
        return self.get_remote_version()


class S3DataSource(DataSource):
    """Data source that downloads from S3 (requires boto3)."""
    
    def __init__(self, url: str):
        super().__init__(url)
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
        
        # Read AWS credentials from config if set
        aws_access_key_id = main_config.get("data", "aws_access_key_id", fallback="")
        aws_secret_access_key = main_config.get("data", "aws_secret_access_key", fallback="")
        if aws_access_key_id and aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        elif (aws_access_key_id and not aws_secret_access_key) or (not aws_access_key_id and aws_secret_access_key):
            raise ConfigError(
                "both or none of aws_access_key_id and aws_secret_access_key must be set"
            )
        else:
            self.s3_client = boto3.client('s3')
    
    def get_remote_version(self) -> Optional[str]:
        """Check for changes using S3 ETag."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=self.key)
            etag = response.get('ETag')
            if etag:
                return etag.strip().strip('"')
        except Exception as e:
            return None
        
    
    def get(self) -> Optional[str]:
        """Download from S3 and return ETag.
        Gets ETag from the response of the download reques.
        """
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self.key)
            shutil.copyfileobj(response['Body'], temp_file)
            etag = response.get('ETag', '').strip('"')

        self.extract_zip_to_remote_dir(Path(temp_file.name), delete=True)
        return etag



def _get_data_source() -> Union[HTTPDataSource, FileDataSource, S3DataSource]:
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


data_source = _get_data_source()
