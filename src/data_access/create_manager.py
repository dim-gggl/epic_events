import os
import sys
import ctypes
from typing import Optional

from sqlalchemy import select

from src.data_access.config import Session
from src.auth.validators import is_valid_username, is_valid_email
from src.auth.hashing import hash_password
from src.crm.models import User, Role
from src.auth.utils import _prompt_password
from src.auth.permissions import DEFAULT_ROLE_PERMISSIONS


def _ensure_root() -> None:
    """Abort if the current process is not run with administrative privileges.

    On POSIX (macOS/Linux), require EUID == 0 (i.e., 'sudo ...').
    On Windows, require an elevated process (Administrator).
    """
    if os.name == "nt":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            is_admin = False
        if not is_admin:
            sys.stderr.write("This command must be run as root.\n")
            return
    else:
        if os.geteuid() != 0:
            sys.stderr.write("This command must be run with root privileges.\n")
            return


def init_manager(username: Optional[str]=None, 
                full_name: Optional[str]=None, 
                email: Optional[str]=None) -> None:
    """Create a 'management' user. Only callable as root."""
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
        role = session.scalar(select(Role).where(Role.name == "management"))
        if not role:
            role = Role(name="management", permissions=DEFAULT_ROLE_PERMISSIONS.get("management", []))
            session.add(role)
            session.flush()

        existing_email = session.scalar(select(User).where(User.email == email))
        if existing_email:
            print("Email already exists.")
            print("Try again later.")
            sys.exit(1)

        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role_id=role.id
        )

        session.add(user)
        session.commit()

    print(f"Management user '{username}' created with success.")
