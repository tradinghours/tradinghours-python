import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from tradinghours.console import (
    create_parser,
    run_status,
    run_import,
    run_serve,
    main,
    EXIT_CODE_EXPECTED_ERROR,
    EXIT_CODE_UNKNOWN_ERROR,
)
from tradinghours.exceptions import ConfigError, NoAccess, DBError


class TestCreateParser:
    """Test argument parser creation."""
    
    def test_parser_has_status_command(self):
        """Test that parser includes status subcommand."""
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"
        assert args.extended is False
    
    def test_parser_status_with_extended(self):
        """Test status command with --extended flag."""
        parser = create_parser()
        args = parser.parse_args(["status", "--extended"])
        assert args.command == "status"
        assert args.extended is True
    
    def test_parser_has_import_command(self):
        """Test that parser includes import subcommand."""
        parser = create_parser()
        args = parser.parse_args(["import"])
        assert args.command == "import"
        assert args.force is False
        assert args.reset is False
    
    def test_parser_import_with_force(self):
        """Test import command with --force flag."""
        parser = create_parser()
        args = parser.parse_args(["import", "--force"])
        assert args.command == "import"
        assert args.force is True
        assert args.reset is False
    
    def test_parser_import_with_reset(self):
        """Test import command with --reset flag."""
        parser = create_parser()
        args = parser.parse_args(["import", "--reset"])
        assert args.command == "import"
        assert args.force is False
        assert args.reset is True
    
    def test_parser_has_serve_command(self):
        """Test that parser includes serve subcommand."""
        parser = create_parser()
        args = parser.parse_args(["serve"])
        assert args.command == "serve"
        assert args.host == "127.0.0.1"
        assert args.port == 8000
    
    def test_parser_serve_with_options(self):
        """Test serve command with custom options."""
        parser = create_parser()
        args = parser.parse_args([
            "serve",
            "--host", "0.0.0.0",
            "--port", "9000"
        ])
        assert args.command == "serve"
        assert args.host == "0.0.0.0"
        assert args.port == 9000
    
    def test_parser_serve_with_uds(self):
        """Test serve command with Unix domain socket."""
        parser = create_parser()
        args = parser.parse_args(["serve", "--uds", "/tmp/tradinghours.sock"])
        assert args.command == "serve"
        assert args.uds == "/tmp/tradinghours.sock"


class TestRunStatus:
    """Test run_status function."""
    
    def test_run_status_basic(self, mocker):
        """Test basic status output."""
        # Mock db.ready()
        mocker.patch("tradinghours.console.db.ready", return_value=None)
        
        # Mock get_local_data_info
        mock_data_info = Mock()
        mock_data_info.download_timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_data_info.version_identifier = "abc123"
        mocker.patch("tradinghours.console.db.get_local_data_info", return_value=mock_data_info)
        
        # Just verify it runs without errors
        run_status(extended=False)
    
    def test_run_status_extended(self, mocker):
        """Test extended status output."""
        mocker.patch("tradinghours.console.db.ready")
        
        mock_data_info = Mock()
        mock_data_info.download_timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_data_info.version_identifier = "abc123"
        mocker.patch("tradinghours.console.db.get_local_data_info", return_value=mock_data_info)
        
        # Mock database queries
        mocker.patch("tradinghours.console.db.get_num_permanently_closed", return_value=5)
        
        # Mock Currency.list_all
        mock_currencies = [Mock() for _ in range(10)]
        mocker.patch("tradinghours.console.Currency.list_all", return_value=mock_currencies)
        
        # Mock Market.list_all
        mock_markets = [Mock() for _ in range(50)]
        mocker.patch("tradinghours.console.Market.list_all", return_value=mock_markets)
                
        # Just verify it runs without errors
        run_status(extended=True)
    
    def test_run_status_extended_no_currency_access(self, mocker):
        """Test extended status when currencies are not accessible."""
        mocker.patch("tradinghours.console.db.ready")
        
        mock_data_info = Mock()
        mock_data_info.download_timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_data_info.version_identifier = "abc123"
        mocker.patch("tradinghours.console.db.get_local_data_info", return_value=mock_data_info)
        
        mocker.patch("tradinghours.console.db.get_num_permanently_closed", return_value=0)
        
        # Currency.list_all raises NoAccess
        mocker.patch("tradinghours.console.Currency.list_all", side_effect=NoAccess("No access"))
        
        mock_markets = [Mock() for _ in range(50)]
        mocker.patch("tradinghours.console.Market.list_all", return_value=mock_markets)
        
        # Just verify it handles NoAccess gracefully
        run_status(extended=True)


class TestRunImport:
    """Test run_import function."""
    
    def test_run_import_with_reset(self, mocker):
        """Test import with reset flag."""
        mock_data_source = Mock()
        mock_data_source.download.return_value = "version123"
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import(reset=True)
        
        mock_data_source.download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version123")
    
    def test_run_import_with_force(self, mocker):
        """Test import with force flag."""
        mock_data_source = Mock()
        mock_data_source.download.return_value = "version456"
        mock_data_source.needs_download.return_value = True
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import(force=True)
        
        mock_data_source.download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version456")
    
    def test_run_import_needs_download(self, mocker):
        """Test import when update is needed."""
        mock_data_source = Mock()
        mock_data_source.needs_download.return_value = True
        mock_data_source.download.return_value = "version789"
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import()
        
        mock_data_source.download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version789")
    
    def test_run_import_no_update_needed(self, mocker):
        """Test import when data is up-to-date."""
        mock_data_source = Mock()
        mock_data_source.needs_download.return_value = False
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        
        run_import()
        
        # Verify download was not called when data is up-to-date
        mock_data_source.download.assert_not_called()
    
    def test_run_import_quiet_mode(self, mocker):
        """Test import in quiet mode."""
        mock_data_source = Mock()
        mock_data_source.needs_download.return_value = False
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        
        # Just verify it runs without errors
        run_import(quiet=True)


class TestRunServe:
    """Test run_serve function."""
    
    def test_run_serve_without_auto_import(self, mocker):
        """Test server without auto-import."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=0)
        mock_data_source = Mock()
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        run_serve(server_config)
        
        mock_run_server.assert_called_once_with(**server_config)
    
    def test_run_serve_with_auto_import(self, mocker):
        """Test server with auto-import enabled."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=60)
        mock_data_source = Mock()
        mock_data_source.get_remote_version.return_value = "etag123"
        mock_data_source.needs_download.return_value = False
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        run_serve(server_config)
        
        mock_run_server.assert_called_once()
    
    def test_run_serve_without_etag_support(self, mocker):
        """Test server warning when source doesn't support ETags."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=60)
        mock_data_source = Mock()
        mock_data_source.get_remote_version.return_value = None
        mock_data_source.source_url = "file:///tmp/data.zip"
        mock_data_source.needs_download.return_value = False
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        
        # Just verify it runs and calls the server
        run_serve(server_config)
        mock_run_server.assert_called_once()
    
    def test_run_serve_import_error(self, mocker):
        """Test server when dependencies are not installed."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=0)
        mock_data_source = Mock()
        mocker.patch("tradinghours.console.get_data_source", return_value=mock_data_source)
        mocker.patch("tradinghours.server.run_server", side_effect=ImportError("No module"))
        
        with pytest.raises(ImportError, match="No module"):
            run_serve({})


class TestMain:
    """Test main function."""
    
    def test_main_status_command(self, mocker):
        """Test main with status command."""
        mocker.patch("sys.argv", ["tradinghours", "status"])
        mock_run_status = mocker.patch("tradinghours.console.run_status")
        
        main()
        
        mock_run_status.assert_called_once_with(extended=False)
    
    def test_main_import_command(self, mocker):
        """Test main with import command."""
        mocker.patch("sys.argv", ["tradinghours", "import", "--force"])
        mock_run_import = mocker.patch("tradinghours.console.run_import")
        
        main()
        
        mock_run_import.assert_called_once_with(reset=False, force=True)
    
    def test_main_serve_command(self, mocker):
        """Test main with serve command."""
        mocker.patch("sys.argv", ["tradinghours", "serve", "--port", "9000"])
        mock_run_serve = mocker.patch("tradinghours.console.run_serve")
        
        main()
        
        mock_run_serve.assert_called_once()
        call_args = mock_run_serve.call_args[0][0]
        assert call_args["port"] == 9000
    
    def test_main_handles_generic_error(self, mocker):
        """Test main handles generic errors gracefully."""
        mocker.patch("sys.argv", ["tradinghours", "status"])
        mocker.patch("tradinghours.console.run_status", side_effect=RuntimeError("Test error"))
        
        # main() catches exceptions and doesn't raise - just verify it completes
        main()
