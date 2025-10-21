import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from urllib.request import HTTPError

from tradinghours.client import HTTPDataSource, FileDataSource, S3DataSource, data_source
from tradinghours.exceptions import TokenError, ClientError, TradingHoursError, ConfigError


class TestHTTPDataSource:
    """Test HTTPDataSource functionality."""
    
    def test_initialization_with_tradinghours_url(self, mocker):
        """Test that HTTPDataSource requires token for tradinghours.com URLs."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        assert source.url == "https://api.tradinghours.com/v4/download"
        assert source.token == "test_token"
    
    def test_initialization_without_token_fails(self, mocker):
        """Test that HTTPDataSource fails for tradinghours.com URLs without token."""
        mocker.patch("tradinghours.client.main_config.get", return_value="")
        with pytest.raises(TokenError):
            HTTPDataSource("https://api.tradinghours.com/v4/download")
    
    def test_initialization_with_custom_url(self):
        """Test that HTTPDataSource works with custom URLs without token."""
        source = HTTPDataSource("https://example.com/data.zip")
        assert source.url == "https://example.com/data.zip"
        assert not hasattr(source, 'token') or source.token is None
    
    def test_get_remote_version_with_etag(self, mocker):
        """Test get_remote_version returns ETag when available."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_response = Mock()
        mock_response.headers.get = lambda key: '"abc123"' if key in ('ETag', 'etag') else None
        
        mocker.patch.object(source, '_make_request', return_value=mock_response)
        
        version = source.get_remote_version()
        assert version == "abc123"
    
    def test_get_remote_version_without_etag(self, mocker):
        """Test get_remote_version returns None when ETag not available."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_response = Mock()
        mock_response.headers.get = lambda key: None
        
        mocker.patch.object(source, '_make_request', return_value=mock_response)
        
        version = source.get_remote_version()
        assert version is None
    
    def test_make_request_with_token(self, mocker):
        """Test that _make_request includes Authorization header with token."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_opener = Mock()
        mock_response = Mock()
        mock_opener.open.return_value = mock_response
        source.opener = mock_opener
        
        result = source._make_request()
        
        assert mock_opener.open.called
        request = mock_opener.open.call_args.args[0]
        assert request.headers.get('Authorization') == 'Bearer test_token'
        assert 'tradinghours-python/' in request.headers.get('User-agent')
    
    def test_make_request_token_error(self, mocker):
        """Test that 401/403 errors raise TokenError."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        # no need for mocking, 'test_token' is invalid
        with pytest.raises(TokenError, match="Token is missing or invalid"):
            source._make_request()
    
    def test_make_request_client_error(self, mocker):
        """Test that other HTTP errors raise ClientError."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_opener = Mock()
        mock_opener.open.side_effect = HTTPError("url", 500, "Server Error", {}, None)
        source.opener = mock_opener
        
        with pytest.raises(ClientError):
            source._make_request()


class TestFileDataSource:
    """Test FileDataSource functionality."""
    
    def test_initialization_with_valid_file(self):
        """Test FileDataSource initialization with existing file."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            file_url = f"file://{tmp_path}"
            source = FileDataSource(file_url)
            assert source.file_path == Path(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_initialization_with_missing_file(self):
        """Test FileDataSource fails with non-existent file."""
        file_url = "file:///nonexistent/path/to/file.zip"
        with pytest.raises(ClientError, match="File not found"):
            FileDataSource(file_url)
    
    def test_get_remote_version_returns_mtime(self):
        """Test get_remote_version returns modification time as string."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            file_url = f"file://{tmp_path}"
            source = FileDataSource(file_url)
            
            version = source.get_remote_version()
            assert version is not None
            assert isinstance(version, str)
            
            # Verify it's a valid float string (timestamp)
            float(version)
        finally:
            os.unlink(tmp_path)
    
    def test_windows_path_handling(self):
        """Test that Windows paths are handled correctly."""        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            source = FileDataSource(f"file://{tmp_path}")
            assert source.file_path == Path(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestS3DataSource:
    """Test S3DataSource functionality."""
    
    def test_initialization_requires_boto3(self, mocker):
        """Test that S3DataSource requires boto3."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', False)
        
        with pytest.raises(TradingHoursError, match="S3 data source requires boto3"):
            S3DataSource("s3://bucket/key")
    
    def test_initialization_with_valid_url(self, mocker):
        """Test S3DataSource initialization with valid S3 URL."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', True)
        mock_boto3 = mocker.patch('tradinghours.client.boto3')
        mocker.patch("tradinghours.client.main_config.get", return_value="")
        
        source = S3DataSource("s3://my-bucket/path/to/file.zip")
        assert source.bucket == "my-bucket"
        assert source.key == "path/to/file.zip"
    
    def test_initialization_with_invalid_url(self, mocker):
        """Test S3DataSource fails with invalid S3 URL."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', True)
        
        with pytest.raises(TradingHoursError, match="Invalid S3 URL"):
            S3DataSource("s3://")
    
    def test_initialization_with_credentials(self, mocker):
        """Test S3DataSource uses credentials from config."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', True)
        mock_boto3 = mocker.patch('tradinghours.client.boto3')
        
        def mock_config_get(section, key, fallback=""):
            if key == "aws_access_key_id":
                return "test_key_id"
            elif key == "aws_secret_access_key":
                return "test_secret_key"
            return fallback
        
        mocker.patch("tradinghours.client.main_config.get", side_effect=mock_config_get)
        
        source = S3DataSource("s3://my-bucket/path/to/file.zip")
        
        mock_boto3.client.assert_called_once_with(
            's3',
            aws_access_key_id="test_key_id",
            aws_secret_access_key="test_secret_key"
        )
    
    def test_initialization_with_partial_credentials_fails(self, mocker):
        """Test S3DataSource fails with only one credential."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', True)
        mock_boto3 = mocker.patch('tradinghours.client.boto3')
        
        def mock_config_get(section, key, fallback=""):
            if key == "aws_access_key_id":
                return "test_key_id"
            return fallback
        
        mocker.patch("tradinghours.client.main_config.get", side_effect=mock_config_get)
        
        with pytest.raises(ConfigError, match="both or none"):
            S3DataSource("s3://my-bucket/path/to/file.zip")
    
    def test_get_remote_version_returns_etag(self, mocker):
        """Test get_remote_version returns S3 ETag."""
        mocker.patch('tradinghours.client.AWS_AVAILABLE', True)
        mock_boto3 = mocker.patch('tradinghours.client.boto3')        
        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {'ETag': '"abc123"'}
        mock_boto3.client.return_value = mock_s3_client
        
        source = S3DataSource("s3://my-bucket/path/to/file.zip")
        version = source.get_remote_version()
        
        assert version == "abc123"
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="my-bucket",
            Key="path/to/file.zip"
        )


class TestDataSourceSingleton:
    """Test the module-level data_source singleton."""
    
    def test_data_source_exists(self):
        """Test that data_source is initialized."""
        assert data_source is not None
        assert hasattr(data_source, 'needs_download')
        assert hasattr(data_source, 'download')
        assert hasattr(data_source, 'get_remote_version')


class TestDataSourceBaseMethods:
    """Test base DataSource methods."""
    
    def test_needs_download_no_local_version(self, mocker):
        """Test needs_download returns True when no local version exists."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mocker.patch("tradinghours.client.db.get_local_data_info", return_value=None)
        
        assert source.needs_download() is True
    
    def test_needs_download_different_versions(self, mocker):
        """Test needs_download returns True when versions differ."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_local_info = Mock()
        mock_local_info.version_identifier = "old_version"
        mocker.patch("tradinghours.client.db.get_local_data_info", return_value=mock_local_info)
        mocker.patch.object(source, 'get_remote_version', return_value="new_version")
        
        assert source.needs_download() is True
    
    def test_needs_download_same_versions(self, mocker):
        """Test needs_download returns False when versions match."""
        mocker.patch("tradinghours.client.main_config.get", return_value="test_token")
        source = HTTPDataSource("https://api.tradinghours.com/v4/download")
        
        mock_local_info = Mock()
        mock_local_info.version_identifier = "same_version"
        mocker.patch("tradinghours.client.db.get_local_data_info", return_value=mock_local_info)
        mocker.patch.object(source, 'get_remote_version', return_value="same_version")
        
        assert source.needs_download() is False






