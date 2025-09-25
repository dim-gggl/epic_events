from functools import wraps

from src.auth.jwt.token_storage import get_access_token
from src.auth.jwt.verify_token import verify_access_token
from src.crm.models import Role
from src.data_access.config import Session

# Constants
ORDERED_DEFAULT_ROLES: list[str] = ["management", "commercial", "support"]

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "support": [
        # Accès lecture à tous les clients, contrats, événements et companies pour assigner support
        "client:list", "client:view",
        "contract:list", "contract:view",
        "event:list", "event:view", "event:update:assigned",
        "company:list", "company:view",
    ],
    "commercial": [
        # Accès complet aux clients, contrats et événements + création companies
        "client:list", "client:view", "client:create", "client:update:own",
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
        "contract:list", "contract:view", "contract:create:existing_relation", "contract:update", "contract:delete",
        # Gestion événements avec contraintes (contrat signé uniquement)
        "event:list", "event:view", "event:create:signed_contract", "event:update", "event:delete",
        # Gestion complète des entreprises
        "company:list", "company:view", "company:create", "company:update", "company:delete"
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
        role_id = get_user_id_and_role_from_token(access_token)[1]
        perms = _permissions_from_db(role_id)
        if perms:
            return required_permission in perms

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

