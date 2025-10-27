import argparse
import traceback

from . import __version__
from .config import print_help, main_config
from .util import timed_action
from .store import Writer, db
from .client import get_data_source
# server import handled in `run_serve` to keep its dependencies optional
from .currency import Currency
from .market import Market
from .exceptions import TradingHoursError, NoAccess
from .config import print_help, main_config, get_logger


logger = get_logger("tradinghours.console")


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
    return parser


def run_status(extended=False):   
    db.ready()
    with timed_action("Collecting data info"):
        local_data_info = db.get_local_data_info()
        local_timestamp = local_data_info.download_timestamp if local_data_info else None
        local_version = local_data_info.version_identifier if local_data_info else None
        
        data_source = get_data_source()
        needs_update = data_source.needs_download()
        if not needs_update:
            version_status = "✗"
        else:
            remote_version = data_source.get_remote_version()
            if remote_version is not None:
                version_status = f"✓ ({remote_version})"
            else:
                version_status = "? (Unable to detect remote version)"

    logger.info("TradingHours Data Status:")
    logger.info(f"  Downloaded at:   {local_timestamp and local_timestamp.ctime()}")
    logger.info(f"  Version:         {local_version}")
    logger.info(f"  New Version Available: {version_status}")
    logger.info("")
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

            logger.info(f"  Currencies count:  {num_all_currencies:4} available")
            logger.info(f"  Markets count:     {num_all_markets:4} available")
            if num_permanently_closed:
                logger.info("")
                logger.info("Notes:")
                logger.info(
                    f"  {num_permanently_closed} permanently closed markets are available but excluded from the totals above.\n"
                    f"  For access to additional markets, please contact us at <sales@tradinghours.com>."
                )
        else:
            logger.info("No local data to show extended information")



def run_import(reset=False, force=False, quiet=False):
    data_source = get_data_source()
    if reset:
        version_identifier = data_source.download()
        Writer().ingest_all(version_identifier)

    elif force or data_source.needs_download():
        version_identifier = data_source.download()
        Writer().ingest_all(version_identifier)

    elif not quiet:
        logger.info("Local data is up-to-date.")

def run_serve(server_config):
    """Run the API server."""
    from .server import run_server
    data_source = get_data_source()
    if main_config.getint("server-mode", "auto_import_frequency"):
        if data_source.get_remote_version() is None:
            logger.warning(f"The `source` {data_source.source_url} does not support HEAD requests or does not return ETags. Please ensure that you set the `auto_import_frequency` to an appropriate value in your `tradinghours.ini` file.")
        run_import(quiet=True)

    run_server(
        **server_config,
    )



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
        logger.exception(f"ERROR: {error}")
        # Log additional debug information
        logger.error(f"VERSION: {__version__}")

        if main_config.get("internal", "mode") == "server":
            log_location = main_config.get("server-mode", "log_folder")
        else:
            log_location = "debug.txt"

        logger.info(
            f"\nDetails about this error were saved to {log_location}. You can "
            "submit it to the support team for further investigation by emailing "
            "support@tradinghours.com.",
        )


if __name__ == "__main__":
    main()
