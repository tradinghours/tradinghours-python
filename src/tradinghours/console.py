import argparse, warnings, time, threading
import traceback

from . import __version__
from .config import print_help
from .store import Writer, db
from .client import (
    download as client_download,
    get_remote_timestamp as client_get_remote_timestamp,
    timed_action
)
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
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    serve_parser.add_argument("--uds", help="Unix domain socket path (overrides host/port)")
    serve_parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    serve_parser.add_argument("--log-level", choices=["debug", "info", "warning", "error"], default="info",
                             help="Log level (default: info)")
    serve_parser.add_argument("--no-auto-update", action="store_true", help="Do not check for data updates every minute")

    return parser


def run_status(extended=False):   
    db.ready()
    with timed_action("Collecting timestamps"):
        remote_timestamp = client_get_remote_timestamp()
        local_timestamp = db.get_local_timestamp()
    print("TradingHours Data Status:")
    print("  Remote Timestamp:  ", remote_timestamp.ctime())
    print("  Local Timestamp:   ", local_timestamp and local_timestamp.ctime())
    print()
    if extended:
        if local_timestamp:
            with timed_action("Reading local data"):
                num_markets, num_currencies = db.get_num_covered()
                num_permanently_closed = db.get_num_permanently_closed()
                try:
                    num_all_currencies = len(list(Currency.list_all()))
                except NoAccess:
                    num_all_currencies = 0
                num_all_markets = len(list(Market.list_all()))
                num_all_markets -= num_permanently_closed

            print(f"  Currencies count:  {num_all_currencies:4} available out of {num_currencies} total")
            print(f"  Markets count:     {num_all_markets:4} available out of {num_markets} total")
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
    show_warning = False
    if reset:
        show_warning = not Writer().ingest_all()

    elif force or db.needs_download():
        client_download()
        show_warning = not Writer().ingest_all()

    elif not quiet:
        print("Local data is up-to-date.")

    if show_warning:
        warnings.warn(
            "\n\nWarning:\nYou seem to be using a MySQL database that is not configured "
            "to handle the full unicode set. Unicode characters have been replaced with "
            "'?'. Consult the MySQL documentation for your version to enable this feature."
        )


def auto_update():
    while True:
        time.sleep(60)
        run_import(quiet=True)


def run_serve(server_config, no_auto_update=False):
    """Run the API server."""
    from .server import run_server
    try:
        if not no_auto_update:
            print("Auto-updating...")
            run_import(quiet=True)
            threading.Thread(target=auto_update, daemon=True).start()

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
            run_serve(server_config, no_auto_update=args.no_auto_update)

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
