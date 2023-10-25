import argparse

from tradinghours.catalog import default_catalog
from tradinghours.remote import default_data_manager


def create_parser():
    parser = argparse.ArgumentParser(description="TradingHours API Client")

    # Create a subparser for the subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    subparsers.required = True

    # "status" subcommand
    status_parser = subparsers.add_parser("status", help="Get status")
    status_parser.add_argument("--bare", action="store_true", help="Print bare status")

    # "import" subcommand
    import_parser = subparsers.add_parser("import", help="Import data")
    import_parser.add_argument("--force", action="store_true", help="Force the import")

    return parser


def run_status(args):
    last_updated = default_data_manager.fetch_last_updated()
    if args.bare:
        print(last_updated.isoformat())
    else:
        print("Remote Last Updated:", last_updated)


def run_import(args):
    if args.force or True:
        print("Downloading...")
        default_data_manager.download()
        print("Ingesting...")
        default_catalog.ingest_all()


def main(args):
    if args.command == "status":
        run_status(args)
    elif args.command == "import":
        run_import(args)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
