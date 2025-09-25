import sentry_sdk
from rich.console import Console

from src.auth.jwt.token_storage import get_access_token
from src.crm.views.views import MainView

view = MainView()

console = Console()
print = console.print



def get_required_token():
    """Get the required access token, showing an error if not available."""
    token = get_access_token()
    if not token:
        view.wrong_message("You must be logged in to perform this action.")
        return None
    return token


def show_error(message, title="Error"):
    """Show an error message with title."""
    view.error_message(f"{title}: {message}")


def run_safely(title, func, *args, **kwargs):
    """Run a function safely and capture exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        show_error(str(e), title)
        return

