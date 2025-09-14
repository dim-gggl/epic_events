import click
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
from src.data_access.create_manager import init_manager, _ensure_root
from src.views.config import epic_style, logo_style
from src.views.views import clear_console

LOGO_PATH = Path("src/views/logo.txt")
console = Console()
print = console.print


# Authentication helper
def get_required_token() -> str | None:
    token = get_access_token()
    if not token:
        print("[bold red]Please login first.[/bold red] Use: [bold]python epic_events.py login[/bold]")
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
    styled_text.append('Usage: ', style="bold gold1")
    parts = line.split(' ', 2)
    if len(parts) > 1:
        styled_text.append(parts[1] + ' ', style="bold orange_red1")
    if len(parts) > 2:
        styled_text.append(parts[2], style="dim medium_spring_green")
    styled_text.append('\n')


def _format_section_header(line: str, styled_text: Text) -> None:
    """Format section headers (lines ending with ':')."""
    styled_text.append(line, style="bold medium_spring_green")
    styled_text.append('\n')


def _format_command_line(line: str, styled_text: Text) -> None:
    """Format command lines (indented with 2 spaces, not 4)."""
    parts = line.strip().split(None, 1)
    styled_text.append('  ', style="grey100")
    
    if parts:
        styled_text.append(parts[0], style="bold orange_red1")
        if len(parts) > 1:
            styled_text.append('  ', style="grey100")
            styled_text.append(parts[1], style="dim grey100")
    else:
        styled_text.append(line, style="grey100")
    
    styled_text.append('\n')


def _format_option_line(line: str, styled_text: Text) -> None:
    """Format option lines (indented with 4 spaces, containing -- or -)."""
    styled_text.append(line, style="dim grey100")
    styled_text.append('\n')


def _format_empty_line(styled_text: Text) -> None:
    """Format empty lines."""
    styled_text.append('\n')


def _format_default_line(line: str, styled_text: Text) -> None:
    """Format any other line with default styling."""
    styled_text.append(line, style="grey100")
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
def command(ctx: click.Context):
    """Epic Events CRM"""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
        
attach_help(command)

# Authentication commands
@command.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-p", "--password", help="Password", required=False)
def login(username, password):
    """Login to the system."""
    main_controller.login(username, password)

@command.command()
def logout():
    """Logout from the system."""
    main_controller.logout()

# Database commands
@command.command()
def db_create():
    """Create the database."""
    init_db()
    
@command.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
def manager_create(username, full_name, email):
    """Create a new manager."""
    has_root = _ensure_root()
    if has_root is False:
        print(Panel("This command must be run with root privileges.\nOn macOS/Linux use: sudo python epic_events.py manager_create ...\nOn Windows run your shell as Administrator.", title="Permission required", border_style="red", box=box.ROUNDED))
    # Always call init_manager; it no-ops if not root
    init_manager(username, full_name, email)

# User commands
@command.group(invoke_without_command=True)
@click.pass_context
def user(ctx: click.Context):
    """User management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(user)

@user.command("create")
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-r", "--role-id", help="Role ID", required=False)
def user_create(username, full_name, email, role_id):
    token = get_required_token()
    if not token:
        return
    main_controller.create_user(token)

@user.command("list")
@click.option("--management", help="Management users", is_flag=True, required=False)
@click.option("--commercial", help="Commercial users", is_flag=True, required=False)
@click.option("--support", help="Support users", is_flag=True, required=False)
def user_list(management=False, commercial=False, support=False):
    token = get_required_token()
    if not token:
        return
    main_controller.list_users(token, management, commercial, support)

@user.command("view")
@click.argument("user_id", type=int)
def user_view(user_id):
    token = get_required_token()
    if not token:
        return
    main_controller.view_user(token, user_id)

@user.command("update")
@click.argument("user_id", type=int)
def user_update(user_id):
    token = get_required_token()
    if not token:
        return
    main_controller.update_user(token, user_id)

@user.command("delete")
@click.argument("user_id", type=int)
def user_delete(user_id):
    token = get_required_token()
    if not token:
        return
    main_controller.delete_user(token, user_id)

# Client commands
@command.group(invoke_without_command=True)
@click.pass_context
def client(ctx: click.Context):
    """Client management commands."""
    if not ctx.invoked_subcommand:
        render_help_with_logo(ctx)
attach_help(client)

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
    main_controller.create_client(
        token, full_name, email, 
        phone, company_id, 
        first_contact_date, 
        last_contact_date
    )

@client.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your clients", default=False)
def client_list(only_mine):
    token = get_required_token()
    if not token:
        return
    main_controller.list_clients(token, only_mine)

@client.command("view")
@click.argument("client_id", type=int)
def client_view(client_id):
    token = get_required_token()
    if not token:
        return
    main_controller.view_client(token, client_id)

@client.command("update")
@click.argument("client_id", type=int)
def client_update(client_id):
    token = get_required_token()
    if not token:
        return
    main_controller.update_client(token, client_id)

@client.command("delete")
@click.argument("client_id", type=int)
def client_delete(client_id):
    token = get_required_token()
    if not token:
        return
    main_controller.delete_client(token, client_id)

# Contract commands
@command.group(invoke_without_command=True)
@click.pass_context
def contract(ctx: click.Context):
    """Contract management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(contract)

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
    main_controller.create_contract(token,
                                    client_id, 
                                    commercial_id, 
                                    total_amount, 
                                    remaining_amount, 
                                    is_signed, 
                                    is_fully_paid)

@contract.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your contracts", default=False)
def contract_list(only_mine):
    token = get_required_token()
    if not token:
        return
    main_controller.list_contracts(token, only_mine)

@contract.command("view")
@click.argument("contract_id", type=int)
def contract_view(contract_id):
    token = get_required_token()
    if not token:
        return
    main_controller.view_contract(token, contract_id)

@contract.command("update")
@click.argument("contract_id", type=int)
def contract_update(contract_id):
    token = get_required_token()
    if not token:
        return
    main_controller.update_contract(token, contract_id)

@contract.command("delete")
@click.argument("contract_id", type=int)
def contract_delete(contract_id):
    token = get_required_token()
    if not token:
        return
    main_controller.delete_contract(token, contract_id)

# Event commands
@command.group(invoke_without_command=True)
@click.pass_context
def event(ctx: click.Context):
    """Event management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(event)

@event.command("create")
def event_create():
    token = get_required_token()
    if not token:
        return
    main_controller.create_event(token)

@event.command("list")
@click.option("--only-mine", 
              is_flag=True, 
              help="Show only your events", 
              default=False)
def event_list(only_mine):
    token = get_required_token()
    if not token:
        return
    main_controller.list_events(token, only_mine)

@event.command("view")
@click.argument("event_id", type=int)
def event_view(event_id):
    token = get_required_token()
    if not token:
        return
    main_controller.view_event(token, event_id)

@event.command("update")
@click.argument("event_id", type=int)
def event_update(event_id):
    token = get_required_token()
    if not token:
        return
    main_controller.update_event(token, event_id)
    
@event.command("assign_support")
@click.argument("event_id", type=int)
@click.argument("support_id", type=int)
def assign_support(event_id, support_id):
    token = get_required_token()
    if not token:
        return
    main_controller.assign_support_to_event(token, event_id, support_id)

@event.command("delete")
@click.argument("event_id", type=int)
def event_delete(event_id):
    token = get_required_token()
    if not token:
        return
    main_controller.delete_event(token, event_id)

# Company commands
@command.group(invoke_without_command=True)
@click.pass_context
def company(ctx: click.Context):
    """Company management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)
attach_help(company)

@company.command("create")
def company_create():
    token = get_required_token()
    if not token:
        return
    main_controller.create_company(token)

@company.command("list")
def company_list():
    token = get_required_token()
    if not token:
        return
    main_controller.list_companies(token)

@company.command("view")
@click.argument("company_id", type=int)
def company_view(company_id):
    token = get_required_token()
    if not token:
        return
    main_controller.view_company(token, company_id)

@company.command("update")
@click.argument("company_id", type=int)
def company_update(company_id):
    token = get_required_token()
    if not token:
        return
    main_controller.update_company(token, company_id)

@company.command("delete")
@click.argument("company_id", type=int)
def company_delete(company_id):
    token = get_required_token()
    if not token:
        return
    main_controller.delete_company(token, company_id)

cli = command
