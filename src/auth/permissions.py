from functools import wraps

from src.auth.jwt.verify_token import verify_access_token
from src.crm.models import Role
from src.data_access.config import Session

# Constants
ORDERED_DEFAULT_ROLES: list[str] = ["management", "commercial", "support"]

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "support": [
        "client:list", "client:view", "contract:list", "contract:view",
        "event:list", "event:view", "event:update:assigned",
    ],
    "commercial": [
        "client:list", "client:view:own", "client:view",
        "contract:list", "contract:view", "event:list", "event:view",
        "client:create", "client:update:own", "contract:update:own",
        "event:create:own_client",
        "company:list", "company:view", "company:create",
    ],
    "management": [
        "user:list", "user:view", "user:create", "user:update", "user:delete",
        "role:list", "role:view", "role:assign",
        "client:list", "client:view", "client:create", "client:update", "client:delete",
        "contract:list", "contract:view", "contract:create", "contract:update", "contract:delete",
        "event:list", "event:view", "event:create", "event:update",
        "company:list", "company:view"
    ],
}

ROLE_ID_TO_NAME: dict[int, str] = {1: "management", 2: "commercial", 3: "support"}

# Helper functions
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
        _, role_id = get_user_id_and_role_from_token(access_token)
        # Try DB-backed permissions first
        perms = _permissions_from_db(role_id)
        if perms is not None:
            return required_permission in perms
        # Fallback to default map
        role_name = ROLE_ID_TO_NAME.get(role_id)
        if not role_name:
            return False
        role_permissions = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        return required_permission in role_permissions
    except Exception:
        return False

# Decorators
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For class methods, access_token is the second argument (after self)
        if len(args) >= 2 and isinstance(args[1], str):
            access_token = args[1]
        elif 'access_token' in kwargs:
            access_token = kwargs['access_token']
        else:
            raise PermissionError("Access token not found in function arguments")

        if not access_token:
            raise PermissionError("Authentication token is required.")
        try:
            verify_access_token(access_token)
        except Exception as e:
            raise PermissionError(f"Invalid token: {e}")
        return func(*args, **kwargs)
    return wrapper

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)

        def wrapper(*args, **kwargs):
            # For class methods, access_token is the second argument (after self)
            if len(args) >= 2 and isinstance(args[1], str):
                access_token = args[1]
            elif 'access_token' in kwargs:
                access_token = kwargs['access_token']
            else:
                raise PermissionError("Access token not found in function arguments")

            if not has_permission(access_token, permission):
                raise PermissionError(
                    f"You don't have permission to "
                    f"{permission.split(':')[1]} {permission.split(':')[0]}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Complex permission checks
def has_permission_for_user(access_token: str, action: str, user_to_view, user_id: int) -> bool:
    if has_permission(access_token, f"user:{action}:any"):
        return True
    if user_to_view.id == user_id:
        return True
    return False
