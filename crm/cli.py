from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.text import Text
from rich.padding import Padding
from rich.layout import Layout
from rich import box
from rich_argparse import RichHelpFormatter

from observability import init_sentry
from db.create_tables import init_db
from db.create_manager import init_manager
from db.crud_client import create_client, list_clients
from db.crud_event import create_event, list_events
from auth.login import login
from auth.register import create_user
from auth.jwt.verify_token import verify_access_token
from exceptions import InvalidUsernameError, InvalidPasswordError
from crm.views.views import MainView
from crm.views.config import epic_style, logo_style
from crm.controllers import MainController as controller
from crm.models import Client

controller = controller()

LOGO_PATH = Path("crm/views/logo.txt")

console = Console()
print = console.print
input = console.input


init_sentry()
view = MainView()

def build_logo_text() -> Text:
    """
    Build the stylized logo Text for help rendering.
    Keep it non-interactive (no input), left-aligned.
    """
    text = LOGO_PATH.read_text(encoding="utf-8")
    t = Text(text, no_wrap=True)
    t.stylize(epic_style, 0, 145)
    t.stylize(logo_style, 145, 147)
    t.stylize(epic_style, 147, 176)
    t.stylize(logo_style, 176, 191)
    t.stylize(epic_style, 191, 194)
    t.stylize(logo_style, 194, 221)
    t.stylize(epic_style, 221, 225)
    t.stylize(logo_style, 225, -1)
    return t

def render_help_with_logo(parser: argparse.ArgumentParser) -> None:
    """
    Render help in two columns using Rich:
    - Left: Epic Events logo (styled)
    - Right: argparse help text for the provided parser
    """
    help_str = parser.format_help()
    logo = build_logo_text()

    try:
        raw_logo = LOGO_PATH.read_text(encoding="utf-8")
        max_logo_width = max((len(line) for line in raw_logo.splitlines()), default=40)
    except Exception:
        max_logo_width = 40

    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, width=max_logo_width + 2)
    grid.add_column(ratio=1)

    left = Padding(logo, (0, 1))
    right = Panel(
        Text.from_ansi(help_str),
        box=box.ROUNDED,
        border_style=epic_style,
        padding=(1, 2),
        title="HELP",
        title_align="left",
    )

    grid.add_row(left, right)
    console.print(grid)

class SideBySideHelpAction(argparse._HelpAction):
    """
    Replace argparse default help to render a Rich 2-column view:
    - Left: logo (fixed width)
    - Right: help text
    """
    def __call__(self, parser, namespace, values, option_string=None):
        render_help_with_logo(parser)
        parser.exit()

def add_side_by_side_help(parser: argparse.ArgumentParser):
    """Disable default help and add our side-by-side help action."""
    for a in list(parser._actions):
        if isinstance(a, argparse._HelpAction):
            parser._actions.remove(a)
            for opt in a.option_strings:
                if opt in parser._option_string_actions:
                    del parser._option_string_actions[opt]
    parser.add_argument("-h", "--help", action=SideBySideHelpAction, help="Show this help message then exit.")


class CustomRichFormatter(RichHelpFormatter):
    """Tweak styles for headings, options and metavars."""
    styles = {
        "argparse.prog": "bold orange_red1",
        "argparse.text": "bright_white",
        "argparse.help": "italic white",
        "argparse.groups": "bold bright_green",
        "argparse.heading": "bold orange_red1",
        "argparse.metavar": "green",
        "argparse.syntax": "bright_yellow",
        "argparse.usage": "bold yellow",
    }
    max_help_position = 32


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epic-events",
        description="[bold orange_red1]Epic Events CLI[/] – operations & user management.",
        epilog="[bold bright_cyan]Tips:[/] use [bold]epic-events help CMD[/] for detailed help on a subcommand.",
        formatter_class=CustomRichFormatter,
        add_help=False,
        usage="python epic_events.py CMD [OPTIONS]"
    )
    add_side_by_side_help(parser)

    global_grp = parser.add_argument_group("Global Options")

    subparsers = parser.add_subparsers(
        title="Commands",
        dest="command",
        metavar="CMD",
        description="Available operational commands.",
    )
    subparsers.required = True

    # init_db
    init_parser = subparsers.add_parser(
        "init-db",
        help="Initialize the database, creating the tables and the necessary data",
        description="Initialize all database structures and seed essentials.",
        formatter_class=CustomRichFormatter,
        aliases=["init_db", "initdb", "init"],
        add_help=False
    )
    add_side_by_side_help(init_parser)

    # init_manager
    create_manager_parser = subparsers.add_parser(
        "init-manager",
        help="Create a new manager user [bold bright_red](requires root privileges)[/]",
        description="Create a management user with [bold bright_red]elevated permissions.[/]",
        formatter_class=CustomRichFormatter,
        aliases=["create_manager", "createsuperuser", "superuser", "createmanager", "create-manager", "init_manager", "initmanager"],
        add_help=False
    )

    mgr_grp = create_manager_parser.add_argument_group("Manager Identity")
    mgr_grp.add_argument("-u", "--username", required=False, help="Username for the manager user")
    mgr_grp.add_argument("-n", "--full-name", dest="full_name", help="Full name of the manager user")
    mgr_grp.add_argument("-e", "--email", required=False, help="Email for the manager user")
    add_side_by_side_help(create_manager_parser)

    # login
    login_parser = subparsers.add_parser(
        "login",
        help="Login to the CRM app",   
        description="Authenticate to obtain a session or token.",
        formatter_class=CustomRichFormatter,
        aliases=["register", "authenticate", "auth"],
        add_help=False
    )
    add_side_by_side_help(login_parser)

    auth_grp = login_parser.add_argument_group("Credentials")
    auth_grp.add_argument("-u", "--username", help="Login ID")
    auth_grp.add_argument("-p", "--password", help="Password (optional)")
    add_side_by_side_help(login_parser)

    # create_user
    create_user_parser = subparsers.add_parser(
        "create-user",
        help="Create a new user [bold bright_red](management only)[/]",
        description="Create a user account; requires a [bold bright_red]management token.[/]",
        formatter_class=CustomRichFormatter,
        aliases=["create_user", "createuser", "register-user", "new-user"],
        add_help=False
    )
    add_side_by_side_help(create_user_parser)
    sec_grp = create_user_parser.add_argument_group("Security")
    sec_grp.add_argument("-t", "--token", help="Access token with management role", required=True)

    ident_grp = create_user_parser.add_argument_group("Identity")
    ident_grp.add_argument("-u", "--username", help="Username for the new user")
    ident_grp.add_argument("-n", "--full-name", dest="full_name", help="Full name of the new user")
    ident_grp.add_argument("-e", "--email", help="Email of the new user")
    ident_grp.add_argument("-p", "--password", help="Password (optional and not recommended. Password is safely prompted without echoing in the terminal)")
    ident_grp.add_argument("-r", "--role-id", type=int, help="Role ID for the new user (1 for Management, 2 for sales or commercial, 3 for support)", default=2)
    
    # create_client
    create_client_parser = subparsers.add_parser(
        "create-client",
        help="Create a new client [bold bright_red](commercial users only)[/]",
        description="Create a new client; requires a [bold bright_red]commercial user token.[/]",
        formatter_class=CustomRichFormatter,
        aliases=["create_client", "createclient", "new-client", "add-client"],  
        add_help=False
    )
    add_side_by_side_help(create_client_parser)
    
    client_sec_grp = create_client_parser.add_argument_group("Security")
    client_sec_grp.add_argument("-t", "--token", help="Access token with commercial role", required=True)

    client_ident_grp = create_client_parser.add_argument_group("Identity")
    client_ident_grp.add_argument("-n", "--full-name", dest="full_name", help="Full name of the new client")
    client_ident_grp.add_argument("-e", "--email", help="Email of the new client")
    client_ident_grp.add_argument("-p", "--phone", help="Phone of the new client")
    client_ident_grp.add_argument("-c", "--company-id", help="Company ID of the new client")
    client_ident_grp.add_argument("-d", "--first-contact-date", help="First contact date of the new client")
    client_ident_grp.add_argument("-l", "--last-contact-date", help="Last contact date of the new client")

    # list_clients
    list_clients_parser = subparsers.add_parser(
        "list-clients",
        help="List all clients or, optionally, only the clients assigned to the current commercial user",
        description="List all clients or, optionally, only the clients assigned to the current commercial user",
        formatter_class=CustomRichFormatter,
        aliases=["list_clients", "listclients", "list-clients"],
        add_help=False
    )
    add_side_by_side_help(list_clients_parser)

    client_sec_grp = list_clients_parser.add_argument_group("Security")
    client_sec_grp.add_argument("-t", "--token", help="Access token", required=True)
    client_sec_grp.add_argument("-f", "--filtered", help="Filter clients by commercial user", required=False, default=False)

    # view_client
    view_client_parser = subparsers.add_parser(
        "view-client",
        help="View a client [bold bright_red](commercial users only)[/]",
        description="View a client",
        formatter_class=CustomRichFormatter,
        aliases=["view_client", "viewclient", "view-client"],
        add_help=False
    )
    add_side_by_side_help(view_client_parser)

    client_sec_grp = view_client_parser.add_argument_group("Security")
    client_sec_grp.add_argument("-t", "--token", help="Access token", required=True)
    client_sec_grp.add_argument("-I", "--client-id", help="Client ID", required=True)
    
    # create_event
    create_event_parser = subparsers.add_parser(
        "create-event",
        help="Create a new event [bold bright_red](commercial users only)[/]",
        description="Create a new event",
        formatter_class=CustomRichFormatter,
        aliases=["create_event", "createevent", "new-event", "add-event"],
        add_help=False
    )
    add_side_by_side_help(create_event_parser)

    event_sec_grp = create_event_parser.add_argument_group("Security")
    event_sec_grp.add_argument("-t", "--token", help="Access token", required=True)

    event_sec_grp = create_event_parser.add_argument_group("Event")
    event_sec_grp.add_argument("-c", "--contract-id", help="Contract ID")
    event_sec_grp.add_argument("-s", "--support-contact-id", help="Support contact ID")
    event_sec_grp.add_argument("-T", "--title", help="Title")
    event_sec_grp.add_argument("-a", "--full-address", help="Full address")
    event_sec_grp.add_argument("-d", "--start-date", help="Start date")
    event_sec_grp.add_argument("-e", "--end-date", help="End date")
    event_sec_grp.add_argument("-p", "--participant-count", help="Participant count")
    event_sec_grp.add_argument("-n", "--notes", help="Notes")

    # list_events
    list_events_parser = subparsers.add_parser(
        "list-events",
        help="List all events or, optionally, only the events assigned to the current support user",
        description="List all events or, optionally, only the events assigned to the current support user",
        formatter_class=CustomRichFormatter,
        aliases=["list_events", "listevents", "list-events"],
        add_help=False
    )
    add_side_by_side_help(list_events_parser)

    event_sec_grp = list_events_parser.add_argument_group("Security")
    event_sec_grp.add_argument("-t", "--token", help="Access token", required=True)
    event_sec_grp.add_argument("-f", "--filtered", help="Filter events by support user", required=False, default=False)

    # "help" subcommand to display help for a specific command
    help_parser = subparsers.add_parser(
        "help",
        help="Show help for a specific command [bold bright_red](requires a token)[/]",
        description="Displays the help menu for a specific command or for all commands if no command is provided.",
        usage="python epic_events.py help [COMMAND]",
        formatter_class=CustomRichFormatter,
        aliases=["help", "h"],
        add_help=False
    )
    help_parser.add_argument("topic", nargs="?", help="Command to show help for")
    add_side_by_side_help(help_parser)

    return parser

def epic_events_crm():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "help":
        sub = args.topic
        if not sub:
            render_help_with_logo(parser)
            return
        sp = parser._subparsers._group_actions[0].choices.get(sub)
        if sp is None:
            print(f"Unknown command: {sub}\n")
            render_help_with_logo(parser)
            return
        render_help_with_logo(sp)
        return

    match args.command:
        case "init-db" | "init_db" | "initdb" | "init":
            init_db()

        case "init-manager" | "init_manager" | "create_manager" | "createsuperuser" \
             | "superuser" | "createmanager" | "initmanager":
            init_manager(getattr(args, 'username', None),
                         getattr(args, "full_name", None),
                         getattr(args, 'email', None))

        case "login" | "register" | "authenticate" | "auth":
            username = getattr(args, "username", None)
            login(username)

        case "create-user" | "create_user" | "createuser" | "register-user" | "new-user":
            access_token = args.token
            create_user(
                access_token,
                getattr(args, 'username', None),
                getattr(args, 'full_name', None),
                getattr(args, 'email', None),
                getattr(args, 'password', None),
                getattr(args, 'role_id', None)
            )

        case "create-client" | "create_client" | "createclient" | "new-client" | "add-client":
            access_token = getattr(args, "token", None)
            create_client(access_token)

        case "list-clients" | "list_clients" | "listclients" | "list-clients":
            access_token = getattr(args, "token", None)
            list_clients(access_token, args.filtered)

        case "view-client" | "view_client" | "show-client" | "client-details" | "showclient" | "read-client" | "detail-client":
            access_token = getattr(args, "token", None)
            client_id = getattr(args, "client_id", None)
            view.display_details(access_token, client_id, Client)
        
        case "create-event" | "create_event" | "createevent" | "new-event" | "add-event":
            access_token = getattr(args, "token", None)
            create_event(access_token)

        case "list-events" | "list_events" | "listevents" | "list-events":
            access_token = getattr(args, "token", None)
            list_events(access_token)


        case _:
            render_help_with_logo(parser)

if __name__ == "__main__":
    epic_events_crm()
