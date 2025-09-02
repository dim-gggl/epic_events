import os
import getpass
import sys

from auth.validators import is_valid_password

def get_secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if not value:
        raise RuntimeError("SECRET_KEY is not set")
    return value

def _prompt_password(confirm: bool = True) -> str:
    """Prompt for a password securely (no echo)."""
    pwd = getpass.getpass("New password: ").strip()
    if not is_valid_password(pwd):
        print("Password should be at least 8 characters long\n"
              "and contain at least one uppercase letter, one\n"
              "lowercase letter and one digit.")
        if not confirm:
            return _prompt_password(confirm=False)
        return _prompt_password()
    if confirm:
        rep = getpass.getpass("Confirm password: ").strip()
        if pwd != rep:
            print("Passwords do not match.")
            sys.exit(1)
        return pwd