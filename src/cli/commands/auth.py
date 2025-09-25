
import click
from rich import box
from rich.panel import Panel
from rich.text import Text

from src.auth.jwt.refresh_token import refresh_tokens
from src.cli.help import epic_help
from src.cli.utils import console, run_safely
from src.crm.controllers.main_controller import main_controller
from src.crm.views.config import epic_style

print = console.print


@click.group()
def auth():
    """Authentication commands."""
    pass


@epic_help
@auth.command()
@click.option("-u", "--username", help="Username", required=False)
@click.option("-p", "--password", help="Password (will prompt securely)", required=False)
def login(username, password):
    """Login to the system."""
    # Never accept passwords via CLI options; prompt securely instead
    run_safely("Login", main_controller.login, username, password)


@epic_help
@auth.command()
def logout():
    """Logout from the system."""
    run_safely("Logout", main_controller.logout)


# Token refresh (rotation)
@epic_help
@auth.command(name="refresh")
def refresh_cmd():
    """Refresh authentication tokens."""
    res = refresh_tokens()
    if not res:
        return
    exp = res[2]
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

