import ctypes
import os
import sys

from sqlalchemy import select

from src.auth.hashing import hash_password
from src.auth.permissions import DEFAULT_ROLE_PERMISSIONS
from src.auth.utils import _prompt_password
from src.auth.validators import is_valid_email, is_valid_username
from src.crm.models import PermissionModel, Role, User
from src.data_access.config import Session


def _ensure_root() -> bool:
    """Check administrative privileges without terminating the process.

    Returns True when the current process has administrative privileges, False otherwise.

    - On POSIX (macOS/Linux), require EUID == 0 (i.e., 'sudo ...').
    - On Windows, require an elevated process (Administrator).
    """
    if os.name == "nt":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            # If we cannot determine admin status, treat as not elevated
            is_admin = False

        if not is_admin:
            sys.stderr.write("This command must be run as root.\n")
            return False
        return True
    else:
        if os.geteuid() != 0:
            sys.stderr.write("This command must be run with root privileges.\n")
            return False
        return True


def init_manager(username: str | None=None,
                full_name: str | None=None,
                email: str | None=None) -> None:
    """Create a 'management' user. Only callable as root."""
    is_root = _ensure_root()
    if is_root is False:
        return

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
            role = Role(name="management")
            session.add(role)
            session.flush()

        # Ensure management permissions both in array and normalized tables
        mgmt_perms = DEFAULT_ROLE_PERMISSIONS.get("management", [])
        role.permissions = list(mgmt_perms)
        # Create missing PermissionModel rows and set association
        perm_rows = []
        for name in mgmt_perms:
            perm = session.scalar(select(PermissionModel).where(PermissionModel.name == name))
            if not perm:
                perm = PermissionModel(name=name)
                session.add(perm)
                session.flush()
            perm_rows.append(perm)
        role.permissions_rel = perm_rows

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
