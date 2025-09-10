from __future__ import annotations
from typing import Dict, List
from functools import wraps

from src.auth.jwt.verify_token import verify_access_token
from src.crm.models import User, Client, Contract, Event

# Constants
ORDERED_DEFAULT_ROLES: List[str] = ["management", "commercial", "support"]

DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "support": [
        "client:list", "client:view", "contract:list", "contract:view",
        "event:list", "event:view", "event:update:assigned",
    ],
    "commercial": [
        "client:list", "client:view:own", "client:view",
        "contract:list", "contract:view", "event:list", "event:view",
        "client:create", "client:update:own", "contract:update:own",
        "event:create:own_client",
    ],
    "management": [
        "user:list", "user:view", "user:create", "user:update", "user:delete",
        "role:list", "role:view", "role:assign",
        "client:list", "client:view", "client:create", "client:update", "client:delete",
        "contract:list", "contract:view", "contract:create", "contract:update", "contract:delete",
        "event:list", "event:view", "event:create", "event:update", "event:delete",
    ],
}

ROLE_ID_TO_NAME: Dict[int, str] = {1: "management", 2: "commercial", 3: "support"}

# Helper functions
def get_user_id_and_role_from_token(access_token: str) -> tuple[int, int]:
    if not access_token:
        raise PermissionError("Authentication token is missing.")
    payload = verify_access_token(access_token)
    user_id = int(payload["sub"])
    role_id = int(payload["role_id"])
    return user_id, role_id

def has_permission(access_token: str, required_permission: str) -> bool:
    try:
        _, role_id = get_user_id_and_role_from_token(access_token)
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
    def wrapper(access_token: str, *args, **kwargs):
        if not access_token:
            raise PermissionError("Authentication token is required.")
        try:
            verify_access_token(access_token)
        except Exception as e:
            raise PermissionError(f"Invalid token: {e}")
        return func(access_token, *args, **kwargs)
    return wrapper

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(access_token: str, *args, **kwargs):
            if not has_permission(access_token, permission):
                raise PermissionError(f"You don't have permission to {permission.replace(':', ' ')}.")
            return func(access_token, *args, **kwargs)
        return wrapper
    return decorator

# Complex permission checks
def has_permission_for_client(access_token: str, action: str, client: Client, user_id: int) -> bool:
    if has_permission(access_token, f"client:{action}:any"):
        return True
    if has_permission(access_token, f"client:{action}:own") and client.commercial_id == user_id:
        return True
    return False

def has_permission_for_contract(access_token: str, action: str, contract: Contract, user_id: int) -> bool:
    if has_permission(access_token, f"contract:{action}:any"):
        return True
    if has_permission(access_token, f"contract:{action}:own") and contract.commercial_id == user_id:
        return True
    return False

def has_permission_for_event(access_token: str, action: str, event: Event, user_id: int) -> bool:
    if has_permission(access_token, f"event:{action}:any"):
        return True
    if has_permission(access_token, f"event:{action}:assigned") and event.support_contact_id == user_id:
        return True
    return False

def has_permission_for_user(access_token: str, action: str, user_to_view: User, user_id: int) -> bool:
    if has_permission(access_token, f"user:{action}:any"):
        return True
    if user_to_view.id == user_id:
        return True
    return False
