import sys

from sqlalchemy import select

from src.auth.decorators import in_session, require_elevated_privileges
from src.auth.hashing import hash_password
from src.auth.permissions import DEFAULT_ROLE_PERMISSIONS
from src.crm.controllers.services import DataService
from src.crm.models import PermissionModel, Role, User
from src.crm.views.views import MainView
from src.data_access.config import Session

session = Session()

view = MainView()


@in_session(session=session)
@require_elevated_privileges
def init_manager(username: str | None=None,
                full_name: str | None=None,
                email: str | None=None) -> None:
    """Create a 'management' user. Only callable as root."""
    data_service = DataService(view)

    username = data_service.treat_username_from_input(username)
    full_name = data_service.treat_full_name_from_input(full_name)
    email = data_service.treat_email_from_input(email)
    password = data_service.treat_password_from_input(confirm=True)

    try:
        password_hash = hash_password(password)
    except ValueError as e:
        view.error_message(f"Password error: {str(e)}")
        return

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
        # Only add permissions that don't already exist for this role
        existing_perms = {p.id for p in role.permissions_rel} if role.permissions_rel else set()
        perm_rows = []
        for name in mgmt_perms:
            perm = session.scalar(select(PermissionModel).where(PermissionModel.name == name))
            if not perm:
                perm = PermissionModel(name=name)
                session.add(perm)
                session.flush()

            # Only add if not already associated with this role
            if perm.id not in existing_perms:
                perm_rows.append(perm)

        # Only update permissions_rel if there are new permissions to add
        if perm_rows:
            if role.permissions_rel:
                role.permissions_rel.extend(perm_rows)
            else:
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
