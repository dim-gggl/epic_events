from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.auth.jwt.refresh_token import refresh_tokens
from src.auth.jwt.token_storage import get_access_token
from src.business_logic.role_logic import role_logic
from src.controllers.main_controller import main_controller
from src.data_access.create_manager import _ensure_root, init_manager
from src.data_access.create_tables import init_db
from src.views.config import epic_style, logo_style
from src.views.views import clear_console

LOGO_PATH = Path("src/views/logo.txt")
console = Console()
print = console.print


def show_error(message: str, title: str = "Error") -> None:
    print(Panel(Text(message, style="bold grey100"), 
                title=Text(title, style=epic_style), 
                border_style=epic_style, 
                box=box.ROUNDED
            )
        )


def run_safely(title: str, func, *args, **kwargs):
    try:
        return True, func(*args, **kwargs)
    except Exception as e:
        try:
            import sentry_sdk  # lazy import to avoid hard dep at import time
            sentry_sdk.capture_exception(e)
        except Exception:
            pass
        show_error(f"{e}", title=title)
        return False, None


# Authentication helper
def get_required_token() -> str | None:
    token = get_access_token()
    if not token:
        print(
            "[bold red]Please login first.[/bold red] "
            "Use: [bold]python epic_events.py login[/bold]"
        )
        return None
    return token

# Help formatting functions for the CLI
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


def _format_usage_line(line: str, styled_text: Text) -> None:
    """Format a usage line with specific styling for command and options."""
    styled_text.append('Usage: ', style=epic_style)
    parts = line.split(' ', 2)
    if len(parts) > 1:
        styled_text.append(parts[1] + ' ', style=logo_style)
    if len(parts) > 2:
        styled_text.append(parts[2], style="bold grey100")
    styled_text.append('\n')


def _format_section_header(line: str, styled_text: Text) -> None:
    """Format section headers (lines ending with ':')."""
    styled_text.append(line, style=epic_style)
    styled_text.append('\n')


def _format_command_line(line: str, styled_text: Text) -> None:
    """Format command lines (indented with 2 spaces, not 4)."""
    parts = line.strip().split(None, 1)
    styled_text.append('  ', style="bold grey100")

    if parts:
        styled_text.append(parts[0], style=logo_style)
        if len(parts) > 1:
            styled_text.append('  ', style="bold grey100")
            styled_text.append(parts[1], style="bold grey100")
    else:
        styled_text.append(line, style="bold grey100")

    styled_text.append('\n')


def _format_option_line(line: str, styled_text: Text) -> None:
    """Format option lines (indented with 4 spaces, containing -- or -)."""
    styled_text.append(line, style="bold grey100")
    styled_text.append('\n')


def _format_empty_line(styled_text: Text) -> None:
    """Format empty lines."""
    styled_text.append('\n')


def _format_default_line(line: str, styled_text: Text) -> None:
    """Format any other line with default styling."""
    styled_text.append(line, style="bold grey100")
    styled_text.append('\n')


def _determine_line_type(line: str) -> str:
    """Determine the type of line for appropriate formatting."""
    line_stripped = line.strip()

    if line_stripped.startswith('Usage:'):
        return 'usage'
    elif line_stripped.endswith(':') and not line.startswith('  '):
        return 'section_header'
    elif line.startswith('  ') and not line.startswith('    '):
        return 'command'
    elif ('--' in line_stripped or line_stripped.startswith('-')) and line.startswith('    '):
        return 'option'
    elif not line_stripped:
        return 'empty'
    else:
        return 'default'


def format_help_with_styles(help_text: str) -> Text:
    """
    Format help text with rich styling for better readability.
    
    Args:
        help_text: Raw help text from Click command
        
    Returns:
        Rich Text object with applied styling
    """
    styled_text = Text()
    lines = help_text.split('\n')

    for line in lines:
        line_type = _determine_line_type(line)

        if line_type == 'usage':
            _format_usage_line(line, styled_text)
        elif line_type == 'section_header':
            _format_section_header(line, styled_text)
        elif line_type == 'command':
            _format_command_line(line, styled_text)
        elif line_type == 'option':
            _format_option_line(line, styled_text)
        elif line_type == 'empty':
            _format_empty_line(styled_text)
        else:
            _format_default_line(line, styled_text)

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

    # Create help text manually to avoid rich-click conflicts
    help_lines = []
    help_lines.append(f"Usage: {ctx.command.name} [OPTIONS]")
    if ctx.command.help:
        help_lines.append("")
        help_lines.append(ctx.command.help)

    if hasattr(ctx.command, 'commands') and ctx.command.commands:
        help_lines.append("")
        help_lines.append("Commands:")
        for name, cmd in ctx.command.commands.items():
            help_lines.append(f"  {name:<15} {cmd.short_help or cmd.help or ''}")

    if hasattr(ctx.command, 'params') and ctx.command.params:
        help_lines.append("")
        help_lines.append("Options:")
        for param in ctx.command.params:
            if isinstance(param, click.Option):
                opts = ', '.join(param.opts)
                help_lines.append(f"  {opts:<20} {param.help or ''}")

    help_text = '\n'.join(help_lines)
    help_content = format_help_with_styles(help_text) if help_text else Text("No help available")
    right = Panel(help_content, 
                  box=box.ROUNDED, 
                  border_style=epic_style, 
                  padding=(1, 2), 
                  title=Text("HELP", 
                  style=epic_style), 
                  title_align="left")
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

def _epic_help_callback(ctx, param, value):
    if value:
        render_help_with_logo(ctx)
        ctx.exit()


def epic_help(cmd):
    return click.option('-h', 
                        '--help', 
                        is_flag=True, 
                        is_eager=True, 
                        expose_value=False,
                        callback=_epic_help_callback, 
                        help='Show this message and exit.')(cmd)


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def command(ctx: click.Context):
    """Epic Events CRM"""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(command)

# Authentication commands
@epic_help
@command.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-p", "--password", help="Password", required=False)
def login(username, password):
    """Login to the system.

    Notes:
    - Passwords are not accepted via CLI options; you will be prompted securely.
    - A refresh token is stored locally (0600) to support `refresh`.
    """
    # Never accept passwords via CLI options; prompt securely instead
    run_safely("Login", main_controller.login, username, password)

@epic_help
@command.command()
def logout():
    """Logout from the system."""
    run_safely("Logout", main_controller.logout)

# Token refresh (rotation)
@epic_help
@command.command(name="refresh")
def refresh_cmd():
    """Refresh and rotate authentication tokens."""
    res = refresh_tokens()
    if not res:
        return
    _, _, exp = res
    print(Panel.fit(
        Text(
            f"Session extended until {exp.strftime('%d/%m/%Y')}", 
            style="bold grey100"), 
            title=Text("Token Refresh", 
            style=epic_style
        ), 
        border_style=epic_style, 
        box=box.ROUNDED
        )
    )

# Database commands
@epic_help
@command.command()
def db_create():
    """Create database tables and seed default roles/permissions (idempotent)."""
    init_db()

@epic_help
@command.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
def manager_create(username, full_name, email):
    """Create a new management user (requires Administrator/root).

    The created user receives full management permissions.
    """
    has_root = _ensure_root()
    if has_root is False:
        print(Panel(
            Text(
                "This command must be run with root privileges.\n"
                "On macOS/Linux use: sudo python epic_events.py manager_create ...\n"
                "On Windows run your shell as Administrator.", style="bold grey100"
            ), 
            title=Text("Permission required", style=epic_style), 
            border_style=epic_style, box=box.ROUNDED
            )
        )
    # Always call init_manager; it no-ops if not root
    init_manager(username, full_name, email)

# User commands
@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def user(ctx: click.Context):
    """User management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(user)

@epic_help
@user.command("create")
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-r", 
              "--role-id", 
              type=int, 
              help="Role ID (1=management, 2=commercial, 3=support)", 
              required=False)
def user_create(username, full_name, email, role_id):
    token = get_required_token()
    if not token:
        return
    # Delegate prompting to controller; only pass token
    run_safely("User Create", main_controller.create_user, token)

@epic_help
@user.command("list")
@click.option("--management", help="Management users", is_flag=True, required=False)
@click.option("--commercial", help="Commercial users", is_flag=True, required=False)
@click.option("--support", help="Support users", is_flag=True, required=False)
def user_list(management=False, commercial=False, support=False):
    token = get_required_token()
    if not token:
        return
    run_safely("User List", main_controller.list_users, token, management, commercial, support)

@epic_help
@user.command("view")
@click.argument("user_id", type=int)
def user_view(user_id):
    token = get_required_token()
    if not token:
        return
    run_safely("User View", main_controller.view_user, token, user_id)

@epic_help
@user.command("update")
@click.argument("user_id", type=int)
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-r", "--role-id", type=int, help="Role ID (1=management, 2=commercial, 3=support)", required=False)
def user_update(user_id, username, full_name, email, role_id):
    token = get_required_token()
    if not token:
        return
    # Controller handles interactive updates
    run_safely("User Update", main_controller.update_user, token, user_id)

@epic_help
@user.command("delete")
@click.argument("user_id", type=int)
def user_delete(user_id):
    token = get_required_token()
    if not token:
        return
    run_safely("User Delete", main_controller.delete_user, token, user_id)

# Client commands
@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def client(ctx: click.Context):
    """Client management commands.

    Tips:
    - `client list --only-mine` shows only clients managed by the logged-in commercial.
    - Dates accept `dd/mm/yyyy` for first/last contact.
    """
    if not ctx.invoked_subcommand:
        render_help_with_logo(ctx)
attach_help(client)

@epic_help
@client.command("create")
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-p", "--phone", help="Phone", required=False)
@click.option("-c", "--company-id", help="Company ID", required=False)
@click.option("-f", "--first-contact-date", help="First contact date", required=False)
@click.option("-l", "--last-contact-date", help="Last contact date", required=False)
def client_create(full_name, email, phone, company_id, first_contact_date, last_contact_date):
    token = get_required_token()
    if not token:
        return
    run_safely("Client Create", main_controller.create_client,
               token, full_name, email, phone, company_id, first_contact_date, last_contact_date)

@epic_help
@client.command("list")
@click.option("--only-mine", is_flag=True, help="Show only clients managed by the logged-in commercial", default=False)
def client_list(only_mine):
    """List clients (optionally restricted to your portfolio)."""
    token = get_required_token()
    if not token:
        return
    run_safely("Client List", main_controller.list_clients, token, only_mine)

@epic_help
@client.command("view")
@click.argument("client_id", type=int)
def client_view(client_id):
    token = get_required_token()
    if not token:
        return
    run_safely("Client View", main_controller.view_client, token, client_id)

@epic_help
@client.command("update")
@click.argument("client_id", type=int)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-p", "--phone", help="Phone", required=False)
@click.option("-c", "--company-id", help="Company ID", required=False)
@click.option("-f", "--first-contact-date", help="First contact date", required=False)
@click.option("-l", "--last-contact-date", help="Last contact date", required=False)
def client_update(client_id, full_name, email, phone, company_id, first_contact_date, last_contact_date):
    token = get_required_token()
    if not token:
        return
    run_safely(
        "Client Update",
        main_controller.update_client,
        token,
        client_id,
        full_name,
        email,
        phone,
        company_id,
        first_contact_date,
        last_contact_date,
    )

@epic_help
@client.command("delete")
@click.argument("client_id", type=int)
def client_delete(client_id):
    token = get_required_token()
    if not token:
        return
    run_safely("Client Delete", main_controller.delete_client, token, client_id)

# Contract commands
@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def contract(ctx: click.Context):
    """Contract management commands.

    Examples:
    - List only your unsigned contracts: `contract list --only-mine --unsigned`
    - List contracts not fully paid: `contract list --unpaid`
    """
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(contract)

@epic_help
@contract.command("create")
@click.option("--client-id", help="Client ID", required=False)
@click.option("--commercial-id", help="Commercial ID", required=False)
@click.option("--total-amount", help="Total amount", required=False)
@click.option("--remaining-amount", help="Remaining amount", required=False)
@click.option("--is-signed", help="Is signed", required=False)
@click.option("--is-fully-paid", help="Is fully paid", required=False)
def contract_create(client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid):
    token = get_required_token()
    if not token:
        return
    run_safely("Contract Create", main_controller.create_contract,
               token, client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid)

@epic_help
@contract.command("list")
@click.option("--only-mine", is_flag=True, help="Show only contracts managed by the logged-in commercial", default=False)
@click.option("--unsigned", is_flag=True, help="Filter to contracts not signed yet", default=False)
@click.option("--unpaid", is_flag=True, help="Filter to contracts not fully paid", default=False)
def contract_list(only_mine, unsigned, unpaid):
    """List contracts with optional filters (combinable)."""
    token = get_required_token()
    if not token:
        return
    run_safely("Contract List", main_controller.list_contracts, token, only_mine, unsigned, unpaid)

@epic_help
@contract.command("view")
@click.argument("contract_id", type=int)
def contract_view(contract_id):
    token = get_required_token()
    if not token:
        return
    run_safely("Contract View", main_controller.view_contract, token, contract_id)

@epic_help
@contract.command("update")
@click.argument("contract_id", type=int)
@click.option("--client-id", help="Client ID", required=False)
@click.option("--commercial-id", help="Commercial ID", required=False)
@click.option("--total-amount", help="Total amount", required=False)
@click.option("--remaining-amount", help="Remaining amount", required=False)
@click.option("--is-signed", help="Is signed", required=False)
@click.option("--is-fully-paid", help="Is fully paid", required=False)
def contract_update(contract_id, client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid):
    token = get_required_token()
    if not token:
        return
    run_safely(
        "Contract Update",
        main_controller.update_contract,
        token,
        contract_id,
        client_id,
        commercial_id,
        total_amount,
        remaining_amount,
        is_signed,
        is_fully_paid,
    )

@epic_help
@contract.command("delete")
@click.argument("contract_id", type=int)
def contract_delete(contract_id):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.delete_contract(token, contract_id)
    except Exception as e:
        show_error(f"{e}", title="Contract Delete")

# Event commands
@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def event(ctx: click.Context):
    """Event management commands.

    Tips:
    - `event list --only-mine` shows events assigned to you (support).
    - `event list --unassigned` lists events without support (management only).
    - Dates accept `dd/mm/yyyy` or `dd/mm/yyyy HH:MM`.
    """
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(event)

@epic_help
@event.command("create")
@click.option("--contract-id", type=int, help="Contract ID", required=False)
@click.option("--title", type=str, help="Event title", required=False)
@click.option("--full-address", type=str, help="Full address", required=False)
@click.option("--support-contact-id", type=int, help="Support user ID", required=False)
@click.option("--start-date", type=str, help="Start date (dd/mm/yyyy or dd/mm/yyyy HH:MM)", required=False)
@click.option("--end-date", type=str, help="End date (dd/mm/yyyy or dd/mm/yyyy HH:MM)", required=False)
@click.option("--participant-count", type=int, help="Participant count", required=False)
@click.option("--notes", type=str, help="Notes", required=False)
def event_create(
    contract_id, title, full_address, 
    support_contact_id, start_date, 
    end_date, participant_count, notes
):
    token = get_required_token()
    if not token:
        return
    try:
        # Pass provided options; controller will prompt for any missing fields
        main_controller.create_event(
            token,
            contract_id,
            title,
            full_address,
            support_contact_id,
            start_date,
            end_date,
            participant_count,
            notes,
        )
    except Exception as e:
        show_error(f"{e}", title="Event Create")

@epic_help
@event.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your events", default=False)
@click.option("--unassigned", is_flag=True, help="Show only unassigned events (management only)", default=False)
def event_list(only_mine, unassigned):
    """List events with optional restriction (`--only-mine`) or unassigned filter."""
    token = get_required_token()
    if not token:
        return
    run_safely("Event List", main_controller.list_events, token, only_mine, unassigned)

@epic_help
@event.command("view")
@click.argument("event_id", type=int)
def event_view(event_id):
    token = get_required_token()
    if not token:
        return
    run_safely("Event View", main_controller.view_event, token, event_id)

@epic_help
@event.command("update")
@click.argument("event_id", type=int)
@click.option("--contract-id", type=int, help="Contract ID", required=False)
@click.option("--title", type=str, help="Event title", required=False)
@click.option("--full-address", type=str, help="Full address", required=False)
@click.option("--support-contact-id", type=int, help="Support user ID", required=False)
@click.option("--start-date", type=str, help="Start date (dd/mm/yyyy or dd/mm/yyyy HH:MM)", required=False)
@click.option("--end-date", type=str, help="End date (dd/mm/yyyy or dd/mm/yyyy HH:MM)", required=False)
@click.option("--participant-count", type=int, help="Participant count", required=False)
@click.option("--notes", type=str, help="Notes", required=False)
def event_update(event_id, 
                 contract_id, 
                 title, 
                 full_address, 
                 support_contact_id, 
                 start_date, 
                 end_date, 
                 participant_count, 
                 notes):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.update_event(
            token,
            event_id,
            contract_id,
            title,
            full_address,
            support_contact_id,
            start_date,
            end_date,
            participant_count,
            notes,
        )
    except Exception as e:
        show_error(f"{e}", title="Event Update")

@epic_help
@event.command("assign_support")
@click.argument("event_id", type=int)
@click.argument("support_id", type=int)
def assign_support(event_id, support_id):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.assign_support_to_event(token, event_id, support_id)
    except Exception as e:
        show_error(f"{e}", title="Event Assign Support")

@epic_help
@event.command("delete")
@click.argument("event_id", type=int)
def event_delete(event_id):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.delete_event(token, event_id)
    except Exception as e:
        show_error(f"{e}", title="Event Delete")

# Company commands
@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def company(ctx: click.Context):
    """Company management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(company)

@epic_help
@company.command("create")
@click.option("-n", "--name", help="Company name", required=False)
def company_create(name):
    """Create a company (name required; missing fields will be prompted)."""
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.create_company(token, name)
    except Exception as e:
        show_error(f"{e}", title="Company Create")

@epic_help
@company.command("list")
def company_list():
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.list_companies(token)
    except Exception as e:
        show_error(f"{e}", title="Company List")

@epic_help
@company.command("view")
@click.argument("company_id", type=int)
def company_view(company_id):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.view_company(token, company_id)
    except Exception as e:
        show_error(f"{e}", title="Company View")

@epic_help
@company.command("update")
@click.argument("company_id", type=int)
@click.option("-n", "--name", help="Company name", required=False)
def company_update(company_id, name):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.update_company(token, company_id)
    except Exception as e:
        show_error(f"{e}", title="Company Update")

@epic_help
@company.command("delete")
@click.argument("company_id", type=int)
def company_delete(company_id):
    token = get_required_token()
    if not token:
        return
    try:
        main_controller.delete_company(token, company_id)
    except Exception as e:
        show_error(f"{e}", title="Company Delete")

cli = command

# -----------------------
# Role administration CLI
# -----------------------

@epic_help
@command.group(invoke_without_command=True)
@click.pass_context
def role(ctx: click.Context):
    """Role and permission administration."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(role)


def _print_role(role_obj):
    table = Table(box=box.MINIMAL, show_header=True)
    table.add_column(header=Text("ID", style=epic_style), justify="right")
    table.add_column(header=Text("Name", style=epic_style), justify="left")
    table.add_column(header=Text("Permissions", style=epic_style), justify="left")
    perms = ", ".join(sorted({p.name for p in getattr(role_obj, "permissions_rel", [])}))
    table.add_row(
        Text(str(role_obj.id), style=logo_style), 
        Text(role_obj.name, style="bold grey100"), 
        Text(perms or "(none)", style="bold grey100")
    )
    print(table, justify="center")


@epic_help
@role.command("list")
def role_list():
    token = get_required_token()
    if not token:
        return
    ok, roles = run_safely("Permission", role_logic.list_roles, token)
    if not ok:
        return
    # Render table
    table = Table(box=box.MINIMAL, show_header=True)
    table.add_column(header=Text("ID", style=epic_style), justify="right")
    table.add_column(header=Text("Name", style=epic_style), justify="left")
    table.add_column(header=Text("#Perms", style=epic_style), justify="right")
    for r in roles:
        count = len(getattr(r, "permissions_rel", []) or [])
        table.add_row(
            Text(str(r.id), style=logo_style), 
            Text(r.name, style="bold grey100"), 
            Text(str(count), style="bold grey100")
        )
    print(table, justify="center")


@epic_help
@role.command("view")
@click.argument("role_id", type=int)
def role_view(role_id):
    token = get_required_token()
    if not token:
        return
    ok, r = run_safely("Permission", role_logic.view_role, token, role_id)
    if not ok:
        return
    if not r:
        print(Panel(
            Text("Role not found.", style="bold grey100"), 
            title=Text("Error", style=epic_style), 
            border_style=epic_style, box=box.ROUNDED
            )
        )
        return
    _print_role(r)


@epic_help
@role.command("grant")
@click.argument("role_id", type=int)
@click.argument("permission", type=str)
def role_grant(role_id, permission):
    token = get_required_token()
    if not token:
        return
    ok, r = run_safely("Permission", role_logic.grant_permission, token, role_id, permission)
    if not ok:
        return
    if not r:
        print(Panel(
            Text("Role not found.", style="bold grey100"), 
            title=Text("Error", style=epic_style), 
            border_style=epic_style, box=box.ROUNDED
            )
        )
        return
    print(
        Panel(
            Text(
                f"Granted '{permission}' to role '{r.name}'", 
                style="bold grey100"
            ), 
            title=Text("Success", style=epic_style), 
            border_style=epic_style, 
            box=box.ROUNDED
        )
    )
    _print_role(r)


@epic_help
@role.command("revoke")
@click.argument("role_id", type=int)
@click.argument("permission", type=str)
def role_revoke(role_id, permission):
    token = get_required_token()
    if not token:
        return
    ok, r = run_safely("Permission", 
                        role_logic.revoke_permission, 
                        token, 
                        role_id, 
                        permission)
    if not ok:
        return
    if not r:
        print(Panel(
            Text("Role not found.", style="bold grey100"), 
            title=Text("Error", style=epic_style), 
            border_style=epic_style, box=box.ROUNDED
            )
        )
        return
    print(Panel(
        Text(f"Revoked '{permission}' from role '{r.name}'", 
        style="bold grey100"), title=Text("Success", style=epic_style), 
        border_style=epic_style, box=box.ROUNDED
        )
    )
    _print_role(r)


@epic_help
@role.command("perms")
def role_perms():
    token = get_required_token()
    if not token:
        return
    ok, names = run_safely("Permission", 
                            role_logic.list_all_permission_names, 
                            token)
    if not ok:
        return

    if not names:
        print(Panel(
            Text("No permissions in database.", style="bold grey100"), 
            title=Text("Permissions", style=epic_style), 
            border_style=epic_style, box=box.ROUNDED
            )
        )
        return
    table = Table(box=box.MINIMAL, show_header=True)
    table.add_column(header=Text("Permission", style=epic_style), justify="left")
    for name in names:
        table.add_row(Text(name, style="grey100"))
    print(Panel.fit(Text("Known permissions in DB", style=logo_style), border_style=epic_style))
    print(table, justify="center")
