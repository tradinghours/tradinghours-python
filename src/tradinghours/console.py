import argparse, warnings
import traceback
from textwrap import wrap

from . import __version__
from .store import Writer, db
from .client import (
    download as client_download,
    get_remote_timestamp as client_get_remote_timestamp,
    timed_action
)
from .currency import Currency
from .market import Market
from .exceptions import TradingHoursError, NoAccess

EXIT_CODE_EXPECTED_ERROR = 1
EXIT_CODE_UNKNOWN_ERROR = 2


def print_help(text):
    lines = wrap(text, initial_indent="  ", subsequent_indent="  ")
    print("\n  --")
    print("\n".join(lines))
    print()



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

    return parser


def run_status(args):
    db.ready()
    with timed_action("Collecting timestamps"):
        remote_timestamp = client_get_remote_timestamp()
        local_timestamp = db.get_local_timestamp()
    print("TradingHours Data Status:")
    print("  Remote Timestamp:  ", remote_timestamp.ctime())
    print("  Local Timestamp:   ", local_timestamp and local_timestamp.ctime())
    print()
    if args.extended:
        if local_timestamp:
            with timed_action("Reading local data"):
                num_markets, num_currencies = db.get_num_covered()
                try:
                    all_currencies = list(Currency.list_all())
                except NoAccess:
                    all_currencies = []
                all_markets = list(Market.list_all())

            print(f"  Currencies count:  {len(all_currencies):4} available of {num_currencies}")
            print(f"  Markets count:     {len(all_markets):4} available of {num_markets}")
        else:
            print("No local data to show extended information")


def run_import(args):
    show_warning = False
    if args.reset:
        with timed_action("Ingesting"):
            show_warning = not Writer().ingest_all()

    elif args.force or db.needs_download():
        client_download()
        with timed_action("Ingesting"):
            show_warning = not Writer().ingest_all()
    else:
        print("Local data is up-to-date.")

    if show_warning:
        warnings.warn(
            "\n\nWarning:\nYou seem to be using a MySQL database that is not configured "
            "to handle the full unicode set. Unicode characters have been replaced with "
            "'?'. Consult the MySQL documentation for your version to enable this feature."
        )

def main():
    try:
        # Main console entrypoint
        parser = create_parser()
        args = parser.parse_args()
        if args.command == "status":
            run_status(args)
        elif args.command == "import":
            run_import(args)

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
                "submit it to the support team for further investigation. Feel "
                "free also to submit the file in a new GitHub issue.",
            )
        except Exception as error:
            print("Failed saving debug information.", error)
        finally:
            exit(EXIT_CODE_UNKNOWN_ERROR)


if __name__ == "__main__":
    main()
