import argparse

from tradinghours.catalog import default_catalog
from tradinghours.currency import Currency
from tradinghours.market import Market
from tradinghours.remote import default_data_manager


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
    remote_timestamp = default_data_manager.remote_timestamp
    local_timestamp = default_data_manager.local_timestamp
    print("TradingHours Data Status:")
    print("  Remote Timestamp:  ", remote_timestamp.ctime())
    print("  Local Timestamp:   ", local_timestamp.ctime())
    print()
    if args.extended:
        if local_timestamp:
            print("Extended Information:")
            all_currencies = list(Currency.list_all())
            print("  Currencies count:  ", len(all_currencies))
            all_markets = list(Market.list_all())
            print("  Markets count:     ", len(all_markets))
        else:
            print("No local data to show extended information")


def run_import(args):
    if args.force or default_data_manager.needs_download:
        print("Downloading...")
        default_data_manager.download()
        print("Ingesting...")
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
