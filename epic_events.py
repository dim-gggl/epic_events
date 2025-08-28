import argparse
from db.create_tables import init_db


def main():
    parser = argparse.ArgumentParser(description="Epic Events CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    init_parser = subparsers.add_parser("init_db", help="Initialize the database")
    
    args = parser.parse_args()

    if args.command == "init_db":
        init_db()
    elif args.command is None:
        parser.print_help()


if __name__ == "__main__":
    main()