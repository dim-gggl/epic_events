import argparse
from db.create_tables import init_db
from db.create_manager import init_manager


description = ""
with open("crm/views/logo.txt", "r") as file:
    for line in file.readlines():
        if not line.endswith("\n"):
            line += "\n"
        description += line

def main():
    parser = argparse.ArgumentParser(description="Epic Events CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    init_parser = subparsers.add_parser("init_db", help="Initialize the database")

    create_manager_parser = subparsers.add_parser("init_manager", help="Create a new manager")
    create_manager_parser.add_argument("--username", "-u", help="Username for the manager")
    create_manager_parser.add_argument("--email", "-e", help="Email for the manager")

    args = parser.parse_args()

    match args.command:
        case "init_db":
            init_db()
        case "init_manager":
            init_manager(getattr(args, 'username', None), getattr(args, 'email', None))
        case _:
            parser.print_help()


if __name__ == "__main__":
    main() 