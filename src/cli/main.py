
import click

from src.cli.commands.auth import login, logout, refresh_cmd
from src.cli.commands.client import client
from src.cli.commands.company import company
from src.cli.commands.contract import contract
from src.cli.commands.database import db_create, manager_create
from src.cli.commands.event import event
from src.cli.commands.user import user
from src.cli.help import attach_help, epic_help, render_help_with_logo


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """Epic Events CRM - Secure event management system with role-based permissions."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(cli)

# Add top-level commands from the auth and db groups
cli.add_command(login)
cli.add_command(logout)
cli.add_command(refresh_cmd, name="refresh")
cli.add_command(db_create, name="db-create")
cli.add_command(manager_create, name="manager-create")

# Add command groups
cli.add_command(user)
cli.add_command(client)
cli.add_command(contract)
cli.add_command(event)
cli.add_command(company)

