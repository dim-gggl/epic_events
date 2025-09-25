
import click

from src.cli.help import epic_help
from src.cli.utils import console
from src.data_access.create_manager import init_manager
from src.data_access.create_tables import init_db

print = console.print


@click.group()
def db():
    """Database commands."""
    pass


@epic_help
@db.command("create")
def db_create():
    """Initialize database tables and default roles."""
    init_db()


@epic_help
@db.command("create-manager")
@click.option("-u", "--username", help="Username", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email address", required=False)
def manager_create(username, full_name, email):
    """Create initial management user (requires root/sudo)."""
    init_manager(username, full_name, email)


