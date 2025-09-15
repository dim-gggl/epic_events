import os

from rich.console import Console

from src.auth.validators import is_valid_password
from src.views.views import MainView

view = MainView()
console = Console()


def get_secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if not value:
        raise RuntimeError("SECRET_KEY is not set")
    return value

def _prompt_password(confirm: bool = True) -> str:
    """Prompt for a password securely (no echo)."""
    pwd = console.input("New password: ", password=True).strip()
    if not is_valid_password(pwd):
        view.wrong_message("Password should be at least 8 characters long\n"
              "and contain at least one uppercase letter, one\n"
              "lowercase letter and one digit.")
        if not confirm:
            return _prompt_password(confirm=False)
        return _prompt_password()
    if confirm:
        rep = console.input("Confirm password: ", password=True).strip()
        if pwd != rep:
            view.wrong_message("Passwords do not match.")
            return
        return pwd
