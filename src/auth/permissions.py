from functools import wraps

from src.auth.jwt.token_storage import get_access_token
from src.auth.jwt.verify_token import verify_access_token
from src.crm.models import Role
from src.data_access.config import Session

# Constants
ORDERED_DEFAULT_ROLES: list[str] = ["management", "commercial", "support"]

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "support": [
        # Support ne peut accéder qu'aux données liées à ses événements assignés
        "client:view:assigned_events", "contract:view:assigned_events",
        "event:list:assigned", "event:view:assigned", "event:update:assigned",
        "company:view:assigned_events",
    ],
    "commercial": [
        # Accès complet aux propres clients, contrats et événements + création companies
        "client:list", "client:view", "client:create", "client:update:own", "client:delete:own",
        "contract:list", "contract:view", "contract:create", "contract:update:own",
        "event:list", "event:view", "event:create:own_client",
        "company:list", "company:view", "company:create",
    ],
    "management": [
        # Gestion des utilisateurs et supervision générale
        "user:list", "user:view", "user:create", "user:update", "user:delete",
        "role:list", "role:view", "role:assign",
        # Supervision clients (lecture seule - pas de modification des relations commerciales)
        "client:list", "client:view",
        # Gestion contrats avec contraintes (client-commercial déjà liés)
        "contract:list", "contract:view", "contract:create:existing_relation",
        "contract:update", "contract:delete",
        # Gestion événements avec contraintes (contrat signé uniquement)
        "event:list", "event:view", "event:create:signed_contract",
        "event:update", "event:delete", "event:assign_support",
        # Gestion complète des entreprises
        "company:list", "company:view", "company:create", "company:update", "company:delete"
    ],
}

ROLE_ID_TO_NAME: dict[int, str] = {4: "management", 5: "commercial", 6: "support"}

# Role constants for robust comparison
class UserRoles:
    MANAGEMENT = "management"
    COMMERCIAL = "commercial"
    SUPPORT = "support"

# Helper functions
def get_user_role_name_from_token() -> str:
    """
    Get user role name from JWT token in a robust way.
    Uses role name instead of fragile role_id for business logic.

    Returns:
        str: Role name ('management', 'commercial', 'support') or 'unknown'
    """
    access_token = get_access_token()
    if not access_token:
        return 'unknown'

    try:
        user_id, role_id = get_user_id_and_role_from_token(access_token)
        role_name = ROLE_ID_TO_NAME.get(role_id, 'unknown')
        return role_name
    except Exception:
        return 'unknown'

def get_user_id_and_role_from_token(access_token: str) -> tuple[int, int]:
    if not access_token:
        raise PermissionError("Authentication token is missing.")
    payload = verify_access_token(access_token)
    user_id = int(payload["sub"])
    role_id = int(payload["role_id"])
    return user_id, role_id

def _permissions_from_db(role_id: int) -> list[str] | None:
    try:
        with Session() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                return
            if getattr(role, "permissions_rel", None):
                return [p.name for p in role.permissions_rel]
            if getattr(role, "permissions", None):
                return list(role.permissions)
    except Exception:
        return None
    return None


def has_permission(access_token: str, required_permission: str) -> bool:
    try:
        role_id = get_user_id_and_role_from_token(access_token)[1]
        perms = _permissions_from_db(role_id)
        if perms:
            return _check_permission_match(required_permission, perms)

        role_name = ROLE_ID_TO_NAME.get(role_id)
        if not role_name:
            return False
        role_permissions = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        return _check_permission_match(required_permission, role_permissions)
    except Exception:
        return False

def _check_permission_match(required: str, available_permissions: list[str]) -> bool:
    """
    Check if required permission matches any of the available permissions.
    Supports both exact matches and wildcard matching for specialized permissions.

    Examples:
    - required="client:update", available=["client:update:own"] -> True (specialized covers general)
    - required="client:update:own", available=["client:update"] -> True (general covers specialized)
    - required="client:update:other", available=["client:update:own"]
      -> False (different specializations)
    """
    # Direct match
    if required in available_permissions:
        return True

    # Check if a specialized permission covers the general permission
    required_parts = required.split(':')
    if len(required_parts) >= 2:
        base_permission = ':'.join(required_parts[:2])  # "client:update"

        # If asking for general permission, check if any specialized version is available
        if len(required_parts) == 2:  # General permission like "client:update"
            specialized_perms = [
                p for p in available_permissions
                if p.startswith(base_permission + ':')
            ]
            return len(specialized_perms) > 0

        # If asking for specialized permission, check if general permission is available
        else:  # Specialized permission like "client:update:own"
            return base_permission in available_permissions

    return False

# Decorators
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For class methods, access_token is the second argument (after self)
        token = get_access_token()
        if not token:
            raise PermissionError("You must sign in to continue")
        try:
            verify_access_token(token)
            return func(*args, **kwargs)
        except Exception as token_error:
            raise PermissionError(f"{token_error}")
    return wrapper

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            access_token = get_access_token()
            if not access_token:
                raise PermissionError("Access token not found in function arguments")

            if not has_permission(access_token, permission):
                raise PermissionError(
                    f"You don't have permission to "
                    f"{permission.split(':')[1]} {permission.split(':')[0]}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

