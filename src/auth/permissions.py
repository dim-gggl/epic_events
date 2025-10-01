from functools import wraps

from src.auth.jwt.token_storage import get_access_token, get_stored_token
from src.auth.jwt.verify_token import verify_access_token
from collections.abc import Sequence

from src.crm.models import Role
from src.data_access.config import Session

# Constants
ORDERED_DEFAULT_ROLES: list[str] = ["management", "commercial", "support"]

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "support": [
        # Support can list and view all entities (filtering applied in managers)
        "client:list", "client:view",
        "contract:list", "contract:view",
        "event:list", "event:view", "event:update:assigned",
        # Specialized permissions kept for compatibility
        "client:view:assigned_events", "contract:view:assigned_events",
        "client:view", "client:list", "contract:view", "contract:list",
        "event:list:assigned", "event:view:assigned",
        "company:view:assigned_events",
    ],
    "commercial": [
        # Full access to own clients, contracts and events + company creation
        "client:list", "client:view", "client:create", "client:update:own", "client:delete:own",
        "contract:list", "contract:view", "contract:create", "contract:update:own",
        "event:list", "event:view", "event:create:own_client",
        "company:list", "company:view", "company:create",
    ],
    "management": [
        # User management and general supervision
        "user:list", "user:view", "user:create", "user:update", "user:delete",
        "role:list", "role:view", "role:assign",
        # Client supervision (read-only - no modification of commercial relationships)
        "client:list", "client:view",
        # Contract management with constraints (client-commercial already linked)
        "contract:list", "contract:view", "contract:create",
        "contract:update", "contract:delete",
        # Event management with constraints (signed contract only)
        "event:list", "event:view", "event:create:signed_contract",
        "event:update", "event:delete", "event:assign_support",
        # Complete company management
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
    stored_token = get_stored_token()
    if stored_token:
        role_id_raw = stored_token.get('role_id')
        try:
            role_id = int(role_id_raw) if role_id_raw is not None else None
        except (TypeError, ValueError):
            role_id = None

        if role_id is not None:
            role_name = ROLE_ID_TO_NAME.get(role_id)
            if role_name:
                return role_name

    access_token = get_access_token()
    if not access_token:
        return 'unknown'

    try:
        _, role_id = get_user_id_and_role_from_token(access_token)
        return ROLE_ID_TO_NAME.get(role_id, 'unknown')
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
                return None

            permissions_rel = getattr(role, "permissions_rel", None)
            if isinstance(permissions_rel, Sequence):
                collected = [p.name for p in permissions_rel if getattr(p, "name", None)]
                if collected:
                    return collected

            permissions = getattr(role, "permissions", None)
            if isinstance(permissions, Sequence) and not isinstance(permissions, (str, bytes)):
                return list(permissions)

            return []
    except Exception as e:
        print(f"Error getting permissions from db: {e}")
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
    - required="client:update", 
        available=["client:update:own"] -> True (specialized covers general)
    - required="client:update:own", 
        available=["client:update"] -> True (general covers specialized)
    - required="client:update:other", 
    available=["client:update:own"]
      -> False (different specializations)
    """
    # Direct match
    if required in available_permissions:
        return True

    required_parts = required.split(':')

    # Specialized permission request (e.g., client:update:own) can be satisfied by general grants
    if len(required_parts) >= 3:
        general_permission = ':'.join(required_parts[:2])
        return general_permission in available_permissions

    # General permission requests must be granted explicitly to avoid privilege escalation
    return False

# Decorators
def login_required(func):
    """
    Decorator to ensure the function is only executed if the user is logged in.
    Must be used on all CRUD methods of the CRM to ensure Anonymous User cannot 
    access any data.

    Raises:
        - PermissionError: if the user is not logged in.
        - Exception: such as InvalidTokenError or ExpiredTokenError (e. g. when 
        calling verify_access_token)
        """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For class methods, access_token is the second argument (after self)
        token = get_access_token()
        if not token:
            raise PermissionError("Authentication required")
        try:
            verify_access_token(token)
            return func(*args, **kwargs)
        except Exception:
            raise PermissionError("Authentication required")
    return wrapper

def require_permission(permission: str):
    """
    Decorator to ensure the function is only executed if the user has the required 
    permission.
    Must be used on all CRUD methods of the CRM to ensure users cannot access data 
    they are not authorized to.

    Raises:
        - PermissionError: if the user is not logged in.
        - Exception: such as InvalidTokenError or ExpiredTokenError (e. g. when 
        calling verify_access_token)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            access_token = get_access_token()
            if not access_token:
                raise PermissionError("Authentication required")

            if not has_permission(access_token, permission):
                raise PermissionError("Permission denied")
            return func(*args, **kwargs)
        return wrapper
    return decorator
