import os, sys
from pathlib import Path
from io import StringIO

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.padding import Padding
from rich import box

from crm.views.views import MainView
from crm.views.config import epic_style, logo_style
from db.crud_client import (
    create_client, list_clients, view_client, 
    update_client, delete_client
)
from db.crud_event import (
    create_event, list_events, view_event, 
    update_event, delete_event, assign_support_to_event
)
from db.crud_contract import (
    create_contract, list_contracts, view_contract, 
    update_contract, delete_contract
)
from db.crud_user import (
    create_user, list_users, view_user, 
    update_user, delete_user
)
from auth.login import login as login_user
from auth.logout import logout as logout_user
from auth.jwt.token_storage import (
    get_access_token, cleanup_token_file, get_user_info
    )
from auth.jwt.refresh_token import refresh_access_token
from crm.views.views import clear_console
from exceptions import InvalidTokenError, ExpiredTokenError


LOGO_PATH = Path("crm/views/logo.txt")
console = Console()
print = console.print

view = MainView()

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = True
click.rich_click.APPEND_METAVARS_HELP = True

click.rich_click.STYLE_OPTION = "bold medium_spring_green"
click.rich_click.STYLE_ARGUMENT = "bold gold1"
click.rich_click.STYLE_COMMAND = "bold orange_red1"
click.rich_click.STYLE_SWITCH = "bold medium_spring_green"
click.rich_click.STYLE_METAVAR = "dim italic grey100"
click.rich_click.STYLE_METAVAR_BRACKET = "dim white"
click.rich_click.STYLE_HEADER_TEXT = "bold medium_spring_green"
click.rich_click.STYLE_FOOTER_TEXT = "dim"
click.rich_click.STYLE_USAGE = "bold gold1"
click.rich_click.STYLE_USAGE_COMMAND = "bold orange_red1"
click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold grey100"
click.rich_click.STYLE_HELPTEXT = "dim grey100"
click.rich_click.STYLE_OPTION_DEFAULT = "dim italic grey96"

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
    """Format help text with rich_click styles applied."""
    styled_text = Text()
    lines = help_text.split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        
        # Usage line
        if line_stripped.startswith('Usage:'):
            styled_text.append('Usage: ', style="bold gold1")  # STYLE_USAGE
            usage_cmd = line_stripped.strip().split(' ')[1] + ' '
            styled_text.append(usage_cmd, style="bold orange_red1")  
            styled_text.append(' '.join(line_stripped.strip().split(' ')[2:]), style="dim medium_spring_green")
            styled_text.append('\n')
        
        # Section headers (Commands:, Options:, etc.)
        elif line_stripped.endswith(':') and not line.startswith('  '):
            styled_text.append(line_stripped, style="bold medium_spring_green")  # STYLE_HEADER_TEXT
            styled_text.append('\n')
        
        # Command/option items (indented lines with command names)
        elif line.startswith('  ') and not line.startswith('    '):
            parts = line_stripped.split(None, 1)
            if parts:
                # Command/option name
                styled_text.append('  ', style="grey100")
                styled_text.append(parts[0], style="bold orange_red1")  # STYLE_COMMAND
                
                # Description if present
                if len(parts) > 1:
                    styled_text.append('  ', style="grey100")
                    styled_text.append(parts[1], style="dim grey100")  # STYLE_HELPTEXT
                styled_text.append('\n')
            else:
                styled_text.append(line, style="grey100")
                styled_text.append('\n')
        
        # Option lines with -- or -
        elif ('--' in line_stripped or line_stripped.startswith('-')) and line.startswith('    '):
            # This is likely an option description continuation
            styled_text.append(line, style="dim grey100")  # STYLE_HELPTEXT
            styled_text.append('\n')
        
        # Empty lines
        elif not line_stripped:
            styled_text.append('\n')
        
        # Regular description lines
        else:
            styled_text.append(line, style="grey100")  # STYLE_HELPTEXT
            styled_text.append('\n')
    
    return styled_text

@clear_console
def render_help_with_logo(ctx: click.Context) -> None:
    """Render help with logo on the left and dynamic help content on the right."""
    
    try:
        raw_logo = LOGO_PATH.read_text(encoding="utf-8")
        max_logo_width = max((len(line) for line in raw_logo.splitlines()), default=40)
    except Exception:
        max_logo_width = 40

    logo = build_logo_text()
    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, width=max_logo_width + 2)
    grid.add_column(ratio=1)

    left = Padding(logo, (0, 1))
    
    # Capture the help output by temporarily redirecting stdout
    help_buffer = StringIO()
    old_stdout = sys.stdout
    sys.stdout = help_buffer
    
    try:
        # Generate help by using Click's built-in help mechanism
        with click.Context(ctx.command, info_name=ctx.info_name, parent=ctx.parent) as help_ctx:
            print(ctx.command.get_help(help_ctx))
    except Exception:
        # Fallback: create basic help content
        print(f"Usage: {ctx.command.name} [OPTIONS] COMMAND [ARGS]...")
        print()
        if hasattr(ctx.command, 'commands') and ctx.command.commands:
            print("Commands:")
            for name, cmd in ctx.command.commands.items():
                desc = cmd.short_help or cmd.help or ""
                print(f"  {name:<12} {desc}")
        if hasattr(ctx.command, 'params') and ctx.command.params:
            print()
            print("Options:")
            for param in ctx.command.params:
                if hasattr(param, 'opts') and param.opts:
                    opts_str = ', '.join(param.opts)
                    help_str = getattr(param, 'help', '') or ''
                    print(f"  {opts_str:<20} {help_str}")
    finally:
        sys.stdout = old_stdout
    
    help_text = help_buffer.getvalue()
    
    # Clean and format the help text with rich_click styles
    help_content = format_help_with_styles(help_text) if help_text else Text("No help available")
    
    right = Panel(
        help_content,
        box=box.ROUNDED,
        border_style=epic_style,
        padding=(1, 2),
        title="HELP",
        title_align="left",
    )

    grid.add_row(left, right)
    console.print(grid)


def resolve_token(token: str | None) -> str:
    """
    Resolve JWT access token from multiple sources.
    
    Priority:
    1. Provided token parameter
    2. Token stored in temporary file
    3. Return empty string if no token available
    """
    # If token provided via CLI option, use it
    if token:
        return token
    
    # Try to get token from temporary file (stored after login)
    stored_token = get_access_token()
    if stored_token:
        return stored_token
    
    # No token available - fail securely
    return ""


def attach_help(group: click.Group) -> None:
    @group.command("help")
    @click.argument("command", required=False)
    @click.pass_context
    def _help(ctx: click.Context, command: str | None) -> None:
        if command:
            cmd = group.get_command(ctx, command)
            if not cmd:
                print(f"Unknown command: {command}")
                # Create a context for the parent group
                parent_ctx = click.Context(group, parent=ctx.parent)
                render_help_with_logo(parent_ctx)
            else:
                # Create a context for the specific command
                cmd_ctx = click.Context(cmd, parent=ctx)
                render_help_with_logo(cmd_ctx)
        else:
            # Create a context for the parent group
            parent_ctx = click.Context(group, parent=ctx.parent)
            render_help_with_logo(parent_ctx)


@click.group(invoke_without_command=True)
@click.pass_context
def command(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)


attach_help(command)


@command.command()
@click.option("-u", "--username", help="Login ID", required=False)
@click.option("-p", "--password", help="Password", required=False)
def login(username: str | None, password: str | None) -> None:
    """Login to the Epic Events CRM system."""
    login_user(username, password)


@command.command()
def logout() -> None:
    """Logout and clear authentication session."""
    logout_user()


@command.command()  
@click.option("-r", "--refresh-token", help="Raw refresh token", required=True)
def refresh(refresh_token: str) -> None:
    """Refresh access token using refresh token."""
    try:
        user_info = get_user_info()
        if not user_info or not user_info.get('user_id'):
            view.wrong_message("No user session found. Please login first.")
            return
            
        user_id = user_info['user_id']
        new_access, new_refresh, refresh_exp, refresh_hash = refresh_access_token(user_id, refresh_token)
        
        view.display_login(new_access, new_refresh, refresh_exp)
        
    except (InvalidTokenError, ExpiredTokenError) as e:
        view.wrong_message(f"Token refresh failed: {str(e)}")
    except Exception as e:
        view.wrong_message(f"Refresh operation failed: {str(e)}")


@command.command()
def status() -> None:
    """Check current authentication status."""
    try:
        token = get_access_token()
        if not token:
            view.warning_message("Not authenticated. Please login first.")
            return
            
        user_info = get_user_info()
        if user_info:
            user_id = user_info.get('user_id', 'Unknown')
            role_id = user_info.get('role_id', 'Unknown')
            
            role_names = {1: 'Management', 2: 'Commercial', 3: 'Support'}
            role_name = role_names.get(int(role_id), f'Role {role_id}')
            
            view.success_message(
                f"Authenticated as User ID: {user_id}\n"
                f"Role: {role_name} ({role_id})\n"
                f"Token available in temporary storage"
            )
        else:
            view.warning_message("Authentication token found but user info unavailable.")
            
    except Exception as e:
        view.wrong_message(f"Status check failed: {str(e)}")


@command.group(invoke_without_command=True)
@click.pass_context
def client(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)


attach_help(client)


@client.command("create")
@click.option("-t", "--token", help="Access token with commercial role", required=False)
def client_create(token: str | None) -> None:
    token = resolve_token(token)
    create_client(token)


@client.command("list")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("--only-mine", is_flag=True, help="Show only your clients", default=False)
def client_list(token: str | None, only_mine: bool) -> None:
    token = resolve_token(token)
    list_clients(token, filtered=only_mine)


@client.command("view")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-i", "--client-id", type=int, required=False, help="Client ID")
def client_view(token: str | None, client_id: int | None) -> None:
    token = resolve_token(token)
    if client_id is None:
        client_id = int(view.get_client_id())
    view_client(token, client_id)


@client.command("update")
@click.argument("client_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-n", "--full-name", help="Client full name", required=False)
@click.option("-e", "--email", help="Client email", required=False)
@click.option("-p", "--phone", help="Client phone", required=False)
def client_update(client_id: int, token: str | None, full_name: str | None, 
                  email: str | None, phone: str | None) -> None:
    """Update a client. Commercial users can only update their own clients."""
    token = resolve_token(token)
    update_client(token, client_id, full_name, email, phone)


@client.command("delete")
@click.argument("client_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def client_delete(client_id: int, token: str | None) -> None:
    """Delete a client. Only management can delete clients."""
    token = resolve_token(token)
    delete_client(token, client_id)


@command.group(invoke_without_command=True)
@click.pass_context
def event(ctx: click.Context) -> None:
    """Event management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)


attach_help(event)


@event.command("create")
@click.option("-t", "--token", help="Access token", required=False)
def event_create(token: str | None) -> None:
    """Create an event. Only management can create events."""
    token = resolve_token(token)
    create_event(token)


@event.command("list")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("--only-mine", is_flag=True, default=False, help="Show only events assigned to you")
def event_list(token: str | None, only_mine: bool) -> None:
    """List all events or, optionally, only the events assigned to the current commercial user."""
    token = resolve_token(token)
    list_events(token, filtered=only_mine)


@event.command("view")
@click.argument("event_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def event_view(event_id: int, token: str | None) -> None:
    """View an event. Only management can view events."""
    token = resolve_token(token)
    view_event(token, event_id)


@event.command("delete")
@click.argument("event_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def event_delete(event_id: int, token: str | None) -> None:
    """Delete an event. Only management can delete events."""
    token = resolve_token(token)
    delete_event(token, event_id)


@event.command("update")
@click.argument("event_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-s", "--support-id", type=int, help="Support contact ID to assign", required=False)
def event_update(event_id: int, token: str | None, support_id: int | None) -> None:
    """Assign a support member to an event. Only management can use this command."""
    token = resolve_token(token)
    assign_support_to_event(token, event_id, support_id)


@event.command("edit")
@click.argument("event_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
@click.option("--support_id", type=int, help="Support contact ID to assign", required=False)
def event_edit(event_id: int, token: str | None, support_id: int | None) -> None:
    """Edit all event details. Management and assigned support can edit events."""
    token = resolve_token(token)
    update_event(token, event_id)


@command.group(invoke_without_command=True)
@click.pass_context
def user(ctx: click.Context) -> None:
    """User management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)


attach_help(user)


@user.command("create")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-u", "--username", help="Username for the new user", required=False)
@click.option("-n", "--full-name", help="Full name of the new user", required=False)
@click.option("-e", "--email", help="Email address of the new user", required=False)
@click.option("-r", "--role-id", type=int, help="Role ID (1=Management, 2=Commercial, 3=Support)", required=False)
def user_create(token: str | None, username: str | None, full_name: str | None, 
                email: str | None, role_id: int | None) -> None:
    """Create a new user. Only management can create users."""
    token = resolve_token(token)
    create_user(token, username, full_name, email, None, role_id)


@user.command("list")
@click.option("-t", "--token", help="Access token", required=False)
def user_list(token: str | None) -> None:
    """List all users. Only management can list users."""
    token = resolve_token(token)
    list_users(token)


@user.command("view")
@click.argument("user_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def user_view(user_id: int, token: str | None) -> None:
    """View a user. Management can view any user, others can only view themselves."""
    token = resolve_token(token)
    view_user(token, user_id)


@user.command("update")
@click.argument("user_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-u", "--username", help="New username", required=False)
@click.option("-n", "--full-name", help="New full name", required=False)
@click.option("-e", "--email", help="New email address", required=False)
@click.option("-r", "--role-id", type=int, help="New role ID", required=False)
def user_update(user_id: int, token: str | None, username: str | None, 
                full_name: str | None, email: str | None, role_id: int | None) -> None:
    """Update a user. Only management can update users."""
    token = resolve_token(token)
    update_user(token, user_id, username=username, full_name=full_name, 
                email=email, role_id=role_id)


@user.command("delete")
@click.argument("user_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def user_delete(user_id: int, token: str | None) -> None:
    """Delete a user. Only management can delete users."""
    token = resolve_token(token)
    delete_user(token, user_id)


@command.group(invoke_without_command=True)
@click.pass_context
def contract(ctx: click.Context) -> None:
    """Contract management commands."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)


attach_help(contract)


@contract.command("create")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("-c", "--client-id", type=int, help="Client ID", required=False)
@click.option("-s", "--commercial-id", type=int, help="Commercial ID", required=False)
@click.option("--total-amount", type=float, help="Total contract amount", required=False)
@click.option("--remaining-amount", type=float, help="Remaining amount", required=False)
@click.option("--signed", is_flag=True, help="Mark contract as signed", required=False)
@click.option("--fully-paid", is_flag=True, help="Mark contract as fully paid", required=False)
def contract_create(token: str | None, client_id: int | None, commercial_id: int | None,
                    total_amount: float | None, remaining_amount: float | None,
                    signed: bool, fully_paid: bool) -> None:
    """Create a contract linking a commercial with a client. Only management can create contracts."""
    token = resolve_token(token)
    create_contract(token, client_id, commercial_id, total_amount, remaining_amount, signed, fully_paid)


@contract.command("list")
@click.option("-t", "--token", help="Access token", required=False)
@click.option("--own", is_flag=True, default=False, help="Show only the contracts of the current user")
def contract_list(token: str | None, own: bool) -> None:
    """List contracts. Access depends on user role."""
    token = resolve_token(token)
    list_contracts(token, filtered=own)


@contract.command("view")
@click.argument("contract_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def contract_view(contract_id: int, token: str | None) -> None:
    """View a contract. Access depends on user role."""
    token = resolve_token(token)
    view_contract(token, contract_id)


@contract.command("update")
@click.argument("contract_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
@click.option("--total-amount", type=float, help="Total contract amount", required=False)
@click.option("--remaining-amount", type=float, help="Remaining amount", required=False)
@click.option("--signed", is_flag=True, help="Mark contract as signed", required=False)
@click.option("--fully-paid", is_flag=True, help="Mark contract as fully paid", required=False)
def contract_update(contract_id: int, token: str | None, total_amount: float | None,
                    remaining_amount: float | None, signed: bool, fully_paid: bool) -> None:
    """Update a contract. Management and owning commercial can update contracts."""
    token = resolve_token(token)
    update_contract(token, contract_id, total_amount=total_amount, remaining_amount=remaining_amount,
                    is_signed=signed, is_fully_paid=fully_paid)


@contract.command("delete")
@click.argument("contract_id", type=int)
@click.option("-t", "--token", help="Access token", required=False)
def contract_delete(contract_id: int, token: str | None) -> None:
    """Delete a contract. Only management can delete contracts."""
    token = resolve_token(token)
    delete_contract(token, contract_id)


# Export the main CLI command group
cli = command

