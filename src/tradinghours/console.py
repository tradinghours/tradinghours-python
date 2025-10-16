import argparse
import traceback

from . import __version__
from .config import print_help, main_config
from .util import timed_action
from .store import Writer, db
from .client import data_source
# server import handled in `run_serve` to keep its dependencies optional
from .currency import Currency
from .market import Market
from .exceptions import TradingHoursError, NoAccess

EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNKNOWN_ERROR = 2


def create_parser():
    parser = argparse.ArgumentParser(description="TradingHours API Client")

    # Create a subparser for the subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    subparsers.required = True

    # "status" subcommand
    status_parser = subparsers.add_parser("status", help="Get status")
    status_parser.add_argument(
        "--extended", action="store_true", help="Show more information"
    )

    # "import" subcommand
    import_parser = subparsers.add_parser("import", help="Import data")
    import_parser.add_argument("--force", action="store_true", help="Force the import")
    import_parser.add_argument("--reset", action="store_true", help="Re-ingest data, without downloading. (Resets the database)")

    # "serve" subcommand
    log_level_choices = ["debug", "info", "warning", "error"]
    log_level_choices += [level.upper() for level in log_level_choices]
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    serve_parser.add_argument("--uds", help="Unix domain socket path (overrides host/port)")
    serve_parser.add_argument("--log-level", choices=log_level_choices, default="info",
                             help="Log level (default: info)")

    return parser


def run_status(extended=False):   
    db.ready()
    with timed_action("Collecting data info"):
        local_data_info = db.get_local_data_info()
        local_timestamp = local_data_info.download_timestamp if local_data_info else None
        local_version = local_data_info.version_identifier if local_data_info else None

    print("TradingHours Data Status:")
    print("  Downloaded at:   ", local_timestamp and local_timestamp.ctime())
    print("  Version:         ", local_version)
    print()
    if extended:
        if local_timestamp:
            with timed_action("Reading local data"):
                num_permanently_closed = db.get_num_permanently_closed()
                try:
                    num_all_currencies = len(list(Currency.list_all()))
                except NoAccess:
                    num_all_currencies = 0
                num_all_markets = len(list(Market.list_all()))
                num_all_markets -= num_permanently_closed

            print(f"  Currencies count:  {num_all_currencies:4} available")
            print(f"  Markets count:     {num_all_markets:4} available")
            if num_permanently_closed:
                print()
                print("Notes:")
                print(
                    f"  {num_permanently_closed} permanently closed markets are available but excluded from the totals above.\n"
                    f"  For access to additional markets, please contact us at <sales@tradinghours.com>."
                )
        else:
            print("No local data to show extended information")


def run_import(reset=False, force=False, quiet=False):
    if reset:
        version_identifier = data_source.download()
        Writer().ingest_all(version_identifier)

    elif force or data_source.needs_download():
        version_identifier = data_source.download()
        Writer().ingest_all(version_identifier)

    elif not quiet:
        print("Local data is up-to-date.")


def run_serve(server_config):
    """Run the API server."""
    from .server import run_server
    try:
        if main_config.getint("server-mode", "auto_import_frequency"):
            if data_source.get_remote_version() is None:
                print(f"The `source` {data_source.source_url} does not support HEAD requests or does not return ETags. Pleas ensure that you set the `auto_import_frequency` to an appropriate value in your `tradinghours.ini` file.")
            run_import(quiet=True)

        run_server(
            **server_config,
        )
    except ImportError as e:
        print("ERROR: Server dependencies not installed.")
        print_help("To use the server feature, install with: pip install tradinghours[server]")
        exit(EXIT_CODE_EXPECTED_ERROR)
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        exit(EXIT_CODE_UNKNOWN_ERROR)


def main():
    try:
        # Main console entrypoint
        parser = create_parser()
        args = parser.parse_args()
        if args.command == "status":
            run_status(extended=args.extended)
        elif args.command == "import":
            run_import(reset=args.reset, force=args.force)
        elif args.command == "serve":
            server_config = {
                "host": args.host,
                "port": args.port,
                "uds": args.uds,
            }
            run_serve(server_config)

    # Handle generic errors gracefully
    except Exception as error:
        # TradingHours errors with help messages are simpler
        if isinstance(error, TradingHoursError) and error.help_message:
            print("ERROR:", error.detail)
            print_help(error.help_message)
            exit(EXIT_CODE_EXPECTED_ERROR)

        # Other errors will generate a traceback dump
        error_message = f"ERROR: {error}"
        print(error_message)

        try:
            # Try saving extra information to local file
            traceback_info = traceback.format_exc()
            version_message = f"\nVERSION: {__version__}"
            with open("debug.txt", "w") as debug_file:
                debug_file.write(error_message)
                debug_file.write(version_message)
                debug_file.write("\n\nTraceback:\n")
                debug_file.write(traceback_info)
            print_help(
                "Details about this error were saved to debug.txt file. You can "
                "submit it to the support team for further investigation by emailing "
                "support@tradinghours.com.",
            )
        except Exception as error:
            print("Failed saving debug information.", error)
        finally:
            exit(EXIT_CODE_UNKNOWN_ERROR)


if __name__ == "__main__":
    main()
