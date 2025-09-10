import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.padding import Padding
from rich import box
from pathlib import Path

from src.controllers.main_controller import main_controller
from src.auth.jwt.token_storage import get_access_token
from src.data_access.create_tables import init_db
from src.data_access.create_manager import init_manager
from views.config import epic_style, logo_style
from views.views import clear_console

LOGO_PATH = Path("views/logo.txt")
console = Console()
print = console.print

# Help formatting functions from the old CLI
@clear_console
def build_logo_text() -> Text:
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

def format_help_with_styles(help_text: str) -> Text:
    styled_text = Text()
    lines = help_text.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('Usage:'):
            styled_text.append('Usage: ', style="bold gold1")
            usage_cmd = line_stripped.strip().split(' ')[1] + ' '
            styled_text.append(usage_cmd, style="bold orange_red1")
            styled_text.append(' '.join(line_stripped.strip().split(' ')[2:]), style="dim medium_spring_green")
            styled_text.append('\n')
        elif line_stripped.endswith(':') and not line.startswith('  '):
            styled_text.append(line_stripped, style="bold medium_spring_green")
            styled_text.append('\n')
        elif line.startswith('  ') and not line.startswith('    '):
            parts = line_stripped.split(None, 1)
            if parts:
                styled_text.append('  ', style="grey100")
                styled_text.append(parts[0], style="bold orange_red1")
                if len(parts) > 1:
                    styled_text.append('  ', style="grey100")
                    styled_text.append(parts[1], style="dim grey100")
                styled_text.append('\n')
            else:
                styled_text.append(line, style="grey100")
                styled_text.append('\n')
        elif ('--' in line_stripped or line_stripped.startswith('-')) and line.startswith('    '):
            styled_text.append(line, style="dim grey100")
            styled_text.append('\n')
        elif not line_stripped:
            styled_text.append('\n')
        else:
            styled_text.append(line, style="grey100")
            styled_text.append('\n')
    return styled_text

@clear_console
def render_help_with_logo(ctx: click.Context) -> None:
    raw_logo = LOGO_PATH.read_text(encoding="utf-8")
    max_logo_width = max((len(line) for line in raw_logo.splitlines()), default=40)
    logo = build_logo_text()
    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, width=max_logo_width + 2)
    grid.add_column(ratio=1)
    left = Padding(logo, (0, 1))
    with click.Context(ctx.command, info_name=ctx.info_name, parent=ctx.parent) as help_ctx:
        help_text = ctx.command.get_help(help_ctx)
    help_content = format_help_with_styles(help_text) if help_text else Text("No help available")
    right = Panel(help_content, box=box.ROUNDED, border_style=epic_style, padding=(1, 2), title="HELP", title_align="left")
    grid.add_row(left, right)
    console.print(grid)

def attach_help(group: click.Group) -> None:
    @group.command("help")
    @click.argument("command", required=False)
    @click.pass_context
    def _help(ctx: click.Context, command: str | None) -> None:
        if command:
            cmd = group.get_command(ctx, command)
            if not cmd:
                print(f"Unknown command: {command}")
                parent_ctx = click.Context(group, parent=ctx.parent)
                render_help_with_logo(parent_ctx)
            else:
                cmd_ctx = click.Context(cmd, parent=ctx)
                render_help_with_logo(cmd_ctx)
        else:
            parent_ctx = click.Context(group, parent=ctx.parent)
            render_help_with_logo(parent_ctx)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """Epic Events CRM"""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
        
attach_help(cli)

# Authentication commands
@cli.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-p", "--password", help="Password", required=False)
def login(username, password):
    """Login to the system."""
    main_controller.login(username, password)

@cli.command()
def logout():
    """Logout from the system."""
    main_controller.logout()

# Database commands
@cli.command()
def db_create():
    """Create the database."""
    init_db()
    
@cli.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
def manager_create(username, full_name, email):
    """Create a new manager."""
    init_manager(username, full_name, email)

# User commands
@cli.group(invoke_without_command=True)
@click.pass_context
def user(ctx: click.Context):
    """User management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(user)

@user.command("create")
def user_create():
    token = get_access_token()
    main_controller.create_user(token)

@user.command("list")
def user_list():
    token = get_access_token()
    main_controller.list_users(token)

@user.command("view")
@click.argument("user_id", type=int)
def user_view(user_id):
    token = get_access_token()
    main_controller.view_user(token, user_id)

@user.command("update")
@click.argument("user_id", type=int)
def user_update(user_id):
    token = get_access_token()
    main_controller.update_user(token, user_id)

@user.command("delete")
@click.argument("user_id", type=int)
def user_delete(user_id):
    token = get_access_token()
    main_controller.delete_user(token, user_id)

# Client commands
@cli.group(invoke_without_command=True)
@click.pass_context
def client(ctx: click.Context):
    """Client management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(client)

@client.command("create")
def client_create():
    token = get_access_token()
    main_controller.create_client(token)

@client.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your clients", default=False)
def client_list(only_mine):
    token = get_access_token()
    main_controller.list_clients(token, only_mine)

@client.command("view")
@click.argument("client_id", type=int)
def client_view(client_id):
    token = get_access_token()
    main_controller.view_client(token, client_id)

@client.command("update")
@click.argument("client_id", type=int)
def client_update(client_id):
    token = get_access_token()
    main_controller.update_client(token, client_id)

@client.command("delete")
@click.argument("client_id", type=int)
def client_delete(client_id):
    token = get_access_token()
    main_controller.delete_client(token, client_id)

# Contract commands
@cli.group(invoke_without_command=True)
@click.pass_context
def contract(ctx: click.Context):
    """Contract management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(contract)

@contract.command("create")
def contract_create():
    token = get_access_token()
    main_controller.create_contract(token)

@contract.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your contracts", default=False)
def contract_list(only_mine):
    token = get_access_token()
    main_controller.list_contracts(token, only_mine)

@contract.command("view")
@click.argument("contract_id", type=int)
def contract_view(contract_id):
    token = get_access_token()
    main_controller.view_contract(token, contract_id)

@contract.command("update")
@click.argument("contract_id", type=int)
def contract_update(contract_id):
    token = get_access_token()
    main_controller.update_contract(token, contract_id)

@contract.command("delete")
@click.argument("contract_id", type=int)
def contract_delete(contract_id):
    token = get_access_token()
    main_controller.delete_contract(token, contract_id)

# Event commands
@cli.group(invoke_without_command=True)
@click.pass_context
def event(ctx: click.Context):
    """Event management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(event)

@event.command("create")
def event_create():
    token = get_access_token()
    main_controller.create_event(token)

@event.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your events", default=False)
def event_list(only_mine):
    token = get_access_token()
    main_controller.list_events(token, only_mine)

@event.command("view")
@click.argument("event_id", type=int)
def event_view(event_id):
    token = get_access_token()
    main_controller.view_event(token, event_id)

@event.command("update")
@click.argument("event_id", type=int)
def event_update(event_id):
    token = get_access_token()
    main_controller.update_event(token, event_id)
    
@event.command("assign_support")
@click.argument("event_id", type=int)
@click.argument("support_id", type=int)
def assign_support(event_id, support_id):
    token = get_access_token()
    main_controller.assign_support_to_event(token, event_id, support_id)

@event.command("delete")
@click.argument("event_id", type=int)
def event_delete(event_id):
    token = get_access_token()
    main_controller.delete_event(token, event_id)

command = cli
