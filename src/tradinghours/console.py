import argparse
import time
from contextlib import contextmanager
from threading import Thread

from tradinghours.catalog import default_catalog
from tradinghours.currency import Currency
from tradinghours.market import Market
from tradinghours.remote import default_data_manager


@contextmanager
def timed_action(message: str):
    start = time.time()
    print(f"{message}...", end="", flush=True)

    done = False

    def print_dots():
        while not done:
            print(".", end="", flush=True)
            time.sleep(0.5)

    thread = Thread(target=print_dots)
    thread.daemon = True
    thread.start()

    yield start

    elapsed = time.time() - start
    done = True
    thread.join()
    print(f" ({elapsed:.3f}s)")


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

    return parser


def run_status(args):
    with timed_action("Collecting timestamps"):
        remote_timestamp = default_data_manager.remote_timestamp
        local_timestamp = default_data_manager.local_timestamp
    print("TradingHours Data Status:")
    print("  Remote Timestamp:  ", remote_timestamp.ctime())
    print("  Local Timestamp:   ", local_timestamp and local_timestamp.ctime())
    print()
    if args.extended:
        if local_timestamp:
            with timed_action("Reading local data"):
                all_currencies = list(Currency.list_all())
                all_markets = list(Market.list_all())
            print("Extended Information:")
            print("  Currencies count:  ", len(all_currencies))
            print("  Markets count:     ", len(all_markets))
        else:
            print("No local data to show extended information")


def run_import(args):
    if args.force or default_data_manager.needs_download:
        with timed_action("Downloading"):
            default_data_manager.download()
        with timed_action("Ingesting"):
            default_catalog.ingest_all()
    else:
        print("Local data is up-to-date.")


def main(args):
    if args.command == "status":
        run_status(args)
    elif args.command == "import":
        run_import(args)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
