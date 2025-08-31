import os
import sys
import getpass
from typing import Optional

from sqlalchemy import select

from db.config import engine, Session
from auth.validators import is_valid_username, is_valid_email, is_valid_password
from auth.hashing import hash_password
from crm.models import User, Role


def _ensure_root() -> None:
    """Abort if the current process is not run with administrative privileges.

    On POSIX (macOS/Linux), require EUID == 0 (i.e., 'sudo ...').
    On Windows, require an elevated process (Administrator).
    """
    if os.name == "nt":
        try:
            import ctypes  # lazy import
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            is_admin = False
        if not is_admin:
            sys.stderr.write("This command must be run as Administrator.\n")
            sys.exit(1)
    else:
        if os.geteuid() != 0:
            sys.stderr.write("This command must be run with sudo (root).\n")
            sys.exit(1)


def _prompt_password(confirm: bool = True) -> str:
    """Prompt for a password securely (no echo)."""
    pwd = getpass.getpass("New password: ").strip()
    if not is_valid_password(pwd):
        print("Password should be at least 8 characters long\n"
              "and contain at least one uppercase letter, one\n"
              "lowercase letter and one digit.")
        return _prompt_password(confirm)
    if confirm:
        rep = getpass.getpass("Confirm password: ").strip()
        if pwd != rep:
            print("Passwords do not match.")
            sys.exit(1)
        return pwd

def init_manager(username: Optional[str]=None, full_name: Optional[str]=None, email: Optional[str]=None) -> None:
    """Create a 'management' user. Only callable as root/sudo."""
    _ensure_root()

    # Collect inputs if missing
    if not username:
        username = input("Username: ").strip()
        if not is_valid_username(username):
            print("Username should be between 5 and 64 characters long.\n"
                  "and should not already be in use.")
            username = input("Username: ").strip()
            if not is_valid_username(username):
                print("Username should be between 5 and 64 characters long.\n"
                      "and should not already be in use.")
                print("Try again later.")
                sys.exit(1)
    
    if not full_name:
        full_name = input("Full name: ").strip()
        choice = input("Is this correct? (y/n): ").strip()
        match choice:
            case "y" | "Y" | "yes" | "Yes":
                pass
            case "n" | "N" | "no" | "No":
                full_name = input("Full name: ").strip()
            case _:
                print("Invalid choice.")
                print("Try again later.")
                sys.exit(1)

    if not email:
        email = input("Email: ").strip()
        if not is_valid_email(email):
            print("Invalid email address.")
            email = input("Email: ").strip()
            if not is_valid_email(email):
                print("Invalid email address.")
                print("Try again later.")
                sys.exit(1)

    password = _prompt_password(confirm=True)
    password_hash = hash_password(password)

    with Session() as session:
        # Ensure 'management' role exists
        role = session.scalar(select(Role).where(Role.name == "management"))
        if not role:
            role = Role(name="management")
            session.add(role)
            session.flush()  # get role.id

        existing_email = session.scalar(select(User).where(User.email == email))
        if existing_email:
            print("Email already exists.")
            print("Try again later.")
            sys.exit(1)

        # Build the user record
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role_id=role.id
        )

        # If you use a permissions array/json on User or Role, you can seed it here.
        # Example (adjust to your model fields):
        # user.permissions = ["manage_users", "view_reports", "create_contracts"]

        session.add(user)
        session.commit()

    print(f"Management user '{username}' created with success.")
