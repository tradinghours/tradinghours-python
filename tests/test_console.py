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
            "--port", "9000",
            "--log-level", "debug"
        ])
        assert args.command == "serve"
        assert args.host == "0.0.0.0"
        assert args.port == 9000
        assert args.log_level == "debug"
    
    def test_parser_serve_with_uds(self):
        """Test serve command with Unix domain socket."""
        parser = create_parser()
        args = parser.parse_args(["serve", "--uds", "/tmp/tradinghours.sock"])
        assert args.command == "serve"
        assert args.uds == "/tmp/tradinghours.sock"


class TestRunStatus:
    """Test run_status function."""
    
    def test_run_status_basic(self, mocker, capsys):
        """Test basic status output."""
        # Mock db.ready()
        mocker.patch("tradinghours.console.db.ready", return_value=None)
        
        # Mock get_local_data_info
        mock_data_info = Mock()
        mock_data_info.download_timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_data_info.version_identifier = "abc123"
        mocker.patch("tradinghours.console.db.get_local_data_info", return_value=mock_data_info)
        
        run_status(extended=False)
        
        captured = capsys.readouterr()
        assert "TradingHours Data Status:" in captured.out
        assert "Downloaded at:" in captured.out
        assert "Version:" in captured.out
        assert "abc123" in captured.out
    
    def test_run_status_extended(self, mocker, capsys):
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
                
        run_status(extended=True)
        
        captured = capsys.readouterr()
        assert "Currencies count:" in captured.out
        assert "10" in captured.out
        assert "Markets count:" in captured.out
        assert "45" in captured.out  # 50 - 5 permanently closed
    
    def test_run_status_extended_no_currency_access(self, mocker, capsys):
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
        
        mocker.patch("tradinghours.console.timed_action")
        
        run_status(extended=True)
        
        captured = capsys.readouterr()
        assert "Currencies count:" in captured.out
        assert "0" in captured.out


class TestRunImport:
    """Test run_import function."""
    
    def test_run_import_with_reset(self, mocker):
        """Test import with reset flag."""
        mock_download = mocker.patch("tradinghours.console.data_source.download", return_value="version123")
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import(reset=True)
        
        mock_download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version123")
    
    def test_run_import_with_force(self, mocker):
        """Test import with force flag."""
        mock_download = mocker.patch("tradinghours.console.data_source.download", return_value="version456")
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import(force=True)
        
        mock_download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version456")
    
    def test_run_import_needs_download(self, mocker):
        """Test import when update is needed."""
        mocker.patch("tradinghours.console.data_source.needs_download", return_value=True)
        mock_download = mocker.patch("tradinghours.console.data_source.download", return_value="version789")
        mock_writer = mocker.patch("tradinghours.console.Writer")
        
        run_import()
        
        mock_download.assert_called_once()
        mock_writer.return_value.ingest_all.assert_called_once_with("version789")
    
    def test_run_import_no_update_needed(self, mocker, capsys):
        """Test import when data is up-to-date."""
        mocker.patch("tradinghours.console.data_source.needs_download", return_value=False)
        mock_download = mocker.patch("tradinghours.console.data_source.download")
        
        run_import()
        
        mock_download.assert_not_called()
        captured = capsys.readouterr()
        assert "Local data is up-to-date." in captured.out
    
    def test_run_import_quiet_mode(self, mocker, capsys):
        """Test import in quiet mode."""
        mocker.patch("tradinghours.console.data_source.needs_download", return_value=False)
        
        run_import(quiet=True)
        
        captured = capsys.readouterr()
        assert captured.out == ""


class TestRunServe:
    """Test run_serve function."""
    
    def test_run_serve_without_auto_import(self, mocker):
        """Test server without auto-import."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=0)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        run_serve(server_config)
        
        mock_run_server.assert_called_once_with(**server_config)
    
    def test_run_serve_with_auto_import(self, mocker, capsys):
        """Test server with auto-import enabled."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=60)
        mocker.patch("tradinghours.console.data_source.get_remote_version", return_value="etag123")
        mocker.patch("tradinghours.console.data_source.needs_download", return_value=False)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        run_serve(server_config)
        
        mock_run_server.assert_called_once()
    
    def test_run_serve_without_etag_support(self, mocker, capsys):
        """Test server warning when source doesn't support ETags."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=60)
        mocker.patch("tradinghours.console.data_source.get_remote_version", return_value=None)
        mocker.patch("tradinghours.console.data_source.source_url", "file:///tmp/data.zip")
        mocker.patch("tradinghours.console.data_source.needs_download", return_value=False)
        mock_run_server = mocker.patch("tradinghours.server.run_server")
        
        server_config = {"host": "127.0.0.1", "port": 8000, "uds": None}
        run_serve(server_config)
        
        captured = capsys.readouterr()
        assert "does not support HEAD requests" in captured.out
    
    def test_run_serve_import_error(self, mocker):
        """Test server when dependencies are not installed."""
        mocker.patch("tradinghours.console.main_config.getint", return_value=0)
        mocker.patch("tradinghours.server.run_server", side_effect=ImportError("No module"))
        
        with pytest.raises(SystemExit) as exc_info:
            run_serve({})
        
        assert exc_info.value.code == EXIT_CODE_EXPECTED_ERROR


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
    
    def test_main_handles_generic_error(self, mocker, capsys):
        """Test main handles generic errors and creates debug.txt."""
        mocker.patch("sys.argv", ["tradinghours", "status"])
        mocker.patch("tradinghours.console.run_status", side_effect=RuntimeError("Test error"))
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == EXIT_CODE_UNKNOWN_ERROR
        mock_open.assert_called_once_with("debug.txt", "w")
