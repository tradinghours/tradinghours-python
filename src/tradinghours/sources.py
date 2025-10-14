"""Data source abstraction for downloading TradingHours data from various sources."""

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .config import main_config
from .exceptions import ClientError, TokenError, TradingHoursError

try:
    import boto3
except ImportError:
    AWS_AVAILABLE = False
else:
    AWS_AVAILABLE = True
        


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def check_for_changes(self, stored_etag: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if the data source has changes.
        
        Args:
            stored_etag: Previously stored ETag or mtime
            
        Returns:
            Tuple of (has_changes, new_etag)
            - has_changes: True if data has changed or can't determine
            - new_etag: New ETag/mtime value, or None if unavailable
        """
        pass
    
    @abstractmethod
    def download(self, destination_path: Path) -> Tuple[Path, Optional[str]]:
        """
        Download the data file.
        
        Args:
            destination_path: Directory to extract data to
            
        Returns:
            Tuple of (path, etag)
            - path: Path where data was extracted
            - etag: ETag or mtime value for change tracking
        """
        pass


class HTTPDataSource(DataSource):
    """Data source that downloads from HTTP/HTTPS URLs."""
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize HTTP data source.
        
        Args:
            url: URL to download from. If None, uses default v4 endpoint.
        """
        if url is None or url == "":
            # Default to v4 download endpoint
            token = main_config.get("auth", "token")
            base_url = main_config.get("internal", "base_url")
            self.url = f"{base_url}download"
            self.token = token
        else:
            self.url = url
            # Check if this is the TradingHours API (needs token)
            if "tradinghours.com" in url:
                self.token = main_config.get("auth", "token")
            else:
                self.token = None
    
    def _make_request(self, method: str = "GET", if_none_match: Optional[str] = None) -> object:
        """Make an HTTP request with appropriate headers."""
        request = Request(self.url)
        request.get_method = lambda: method
        
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        
        request.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        
        if if_none_match:
            request.add_header("If-None-Match", if_none_match)
        
        try:
            return urlopen(request)
        except HTTPError as error:
            if error.code == 304:
                # Not modified - this is actually expected for HEAD requests
                return error
            if error.code == 401:
                raise TokenError("Token is missing or invalid")
            if error.code == 404:
                raise ClientError(f"File not found at {self.url}")
            raise ClientError(f"Error getting server response: {error}")
    
    def check_for_changes(self, stored_etag: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check for changes using ETag or Last-Modified header."""
        try:
            response = self._make_request(method="HEAD", if_none_match=stored_etag)
            
            # Check for 304 Not Modified
            if hasattr(response, 'code') and response.code == 304:
                return False, stored_etag
            
            # Try to get ETag
            etag = response.headers.get('ETag') or response.headers.get('etag')
            if etag:
                # Normalize ETag (remove quotes if present)
                etag = etag.strip().strip('"')
                has_changes = (etag != stored_etag) if stored_etag else True
                return has_changes, etag
            
            # Fall back to Last-Modified
            last_modified = response.headers.get('Last-Modified') or response.headers.get('last-modified')
            if last_modified:
                has_changes = (last_modified != stored_etag) if stored_etag else True
                return has_changes, last_modified
            
            # No change detection available - assume changes
            return True, None
            
        except Exception as e:
            # On error, assume changes (fail open)
            print(f"Warning: Could not check for changes: {e}")
            return True, None
    
    def download(self, destination_path: Path) -> Tuple[Path, Optional[str]]:
        """Download data file and extract it."""
        response = self._make_request(method="GET")
        
        # Get ETag for tracking
        etag = response.headers.get('ETag') or response.headers.get('etag')
        if etag:
            etag = etag.strip().strip('"')
        else:
            # Fall back to Last-Modified
            etag = response.headers.get('Last-Modified') or response.headers.get('last-modified')
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()
            temp_path = temp_file.name
        
        return Path(temp_path), etag


class FileDataSource(DataSource):
    """Data source that reads from local filesystem."""
    
    def __init__(self, url: str):
        """
        Initialize file data source.
        
        Args:
            url: file:// URL pointing to local zip file
        """
        # Parse file:// URL to local path
        parsed = urlparse(url)
        if parsed.scheme != 'file':
            raise ValueError(f"FileDataSource requires file:// URL, got: {url}")
        
        # Handle both Unix and Windows paths
        path = unquote(parsed.path)
        
        # On Windows, file:///C:/path becomes /C:/path, need to remove leading /
        if os.name == 'nt' and path.startswith('/') and len(path) > 2 and path[2] == ':':
            path = path[1:]
        
        self.file_path = Path(path)
        
        if not self.file_path.exists():
            raise ClientError(f"File not found: {self.file_path}")
    
    def check_for_changes(self, stored_etag: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check for changes using file modification time."""
        try:
            mtime = os.path.getmtime(self.file_path)
            mtime_str = str(mtime)
            
            if stored_etag is None:
                return True, mtime_str
            
            has_changes = (mtime_str != stored_etag)
            return has_changes, mtime_str
            
        except Exception as e:
            print(f"Warning: Could not check file mtime: {e}")
            return True, None
    
    def download(self, destination_path: Path) -> Tuple[Path, Optional[str]]:
        """Copy file and return path with mtime."""
        # Get mtime for tracking
        mtime = os.path.getmtime(self.file_path)
        mtime_str = str(mtime)
        
        # Copy to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            with open(self.file_path, 'rb') as source_file:
                shutil.copyfileobj(source_file, temp_file)
            temp_path = temp_file.name
        
        return Path(temp_path), mtime_str


class S3DataSource(DataSource):
    
    def __init__(self, url: str):
        if not AWS_AVAILABLE:
            raise TradingHoursError(
                "S3 data source requires boto3. Install with: pip install tradinghours[s3]"
            )
        
        parsed = urlparse(url)
        self.bucket = parsed.netloc
        print(self.bucket)
        self.key = parsed.path.lstrip('/')
        print(self.key)
        
        if not self.bucket or not self.key:
            raise TradingHoursError(f"Invalid S3 URL: {url}, please use the S3 URI in the format s3://bucket/key")
        
        self.s3_client = boto3.client('s3')
    
    def check_for_changes(self, stored_etag: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check for changes using S3 ETag."""
        try:
            # Use head_object to get metadata
            params = {
                'Bucket': self.bucket,
                'Key': self.key
            }
            
            if stored_etag:
                params['IfNoneMatch'] = stored_etag
            
            try:
                response = self.s3_client.head_object(**params)
                etag = response.get('ETag', '').strip('"')
                if stored_etag:
                    has_changes = (etag != stored_etag.strip('"'))
                else:
                    has_changes = True
                
                return has_changes, etag
                
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '304':
                    # Not modified
                    return False, stored_etag
                raise
                
        except Exception as e:
            print(f"Warning: Could not check S3 object: {e}")
            return True, None
    
    def download(self, destination_path: Path) -> Tuple[Path, Optional[str]]:
        # Download to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            self.s3_client.download_fileobj(self.bucket, self.key, temp_file)
            temp_path = temp_file.name
        
        # Get ETag
        response = self.s3_client.head_object(Bucket=self.bucket, Key=self.key)
        etag = response.get('ETag', '').strip('"')
        
        return Path(temp_path), etag


def get_data_source(source_url: Optional[str] = None) -> DataSource:
    """
    Factory function to create appropriate DataSource based on URL scheme.
    
    Args:
        source_url: URL to data source. If None, reads from config.
        
    Returns:
        Appropriate DataSource instance
    """
    if source_url is None:
        source_url = main_config.get("data", "source", fallback="")
    
    if not source_url or source_url == "":
        return HTTPDataSource()
    
    parsed = urlparse(source_url)
    scheme = parsed.scheme.lower()
    
    if scheme in ('http', 'https'):
        return HTTPDataSource(source_url)
    elif scheme == 'file':
        return FileDataSource(source_url)
    elif scheme == 's3':
        return S3DataSource(source_url)
    else:
        raise ValueError(
            f"Unsupported data source scheme: {scheme}. "
            f"Supported schemes: http, https, file, s3"
        )

