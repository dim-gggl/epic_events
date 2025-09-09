from __future__ import annotations

from typing import Dict, List
from crm.views.views import MainView
from auth.jwt.verify_token import verify_access_token
from constants import *


ORDERED_DEFAULT_ROLES: List[str] = [
    "management",
    "commercial",
    "support",
]

view = MainView()


def _check_token_validity(access_token: str) -> bool:
    """Check if access token is valid and not empty."""
    return bool(access_token and access_token.strip())


def _get_role_id(access_token: str) -> int:
    """Get role ID from access token."""
    payload = verify_access_token(access_token)
    return int(payload["role_id"])


def login_required(func):
    """Decorator to require valid authentication token."""
    def wrapper(access_token: str, *args, **kwargs):
        if not _check_token_validity(access_token):
            view.wrong_message(f"{OPERATION_DENIED}: {NOT_AUTH_TOKEN}")
            return
        return func(access_token, *args, **kwargs)
    return wrapper


def role_required(required_role_id: int, role_name: str):
    """Decorator factory for role-specific permissions."""
    def decorator(func):
        def wrapper(access_token: str, *args, **kwargs):
            if not _check_token_validity(access_token):
                view.wrong_message(f"{OPERATION_DENIED}: {NOT_AUTH_TOKEN}")
                return
            if _get_role_id(access_token) != required_role_id:
                view.wrong_message(f"{OPERATION_DENIED}: {ONLY_MANAGEMENT}")
                return
            return func(access_token, *args, **kwargs)
        return wrapper
    return decorator


def commercial_exclusive(func):
    """Decorator for commercial-only operations."""
    return role_required(2, "commercial")(func)


def management_exclusive(func):
    """Decorator for management-only operations."""
    return role_required(1, "management")(func)


def support_exclusive(func):
    """Decorator for support-only operations."""
    return role_required(3, "support")(func)
            
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "support": [
        # Read access to all main resources  
        "client:list",
        "client:view",
        "contract:list", 
        "contract:view",
        "event:list",
        "event:view",
        # Original support permissions
        "event:update:assigned",
        "event:comment:assigned",
    ],
    "commercial": [
        # Read access to all main resources
        "client:list",
        "client:view:own",
        "client:list:own",
        "client:view", 
        "contract:list",
        "contract:view",
        "event:list",
        "event:view",
        # Original commercial permissions
        "client:create",
        "client:update:own",
        "contract:update:own",
        "event:create:own_client",
        "event:comment:own_client",
    ],
    "management": [
        "user:list",
        "user:view",
        "user:create",
        "user:update",
        "user:delete",
        "role:list",
        "role:view",
        "role:assign",
        "client:list",
        "client:view",
        "contract:list",
        "contract:view",
        "contract:create",
        "contract:update",
        "contract:delete",
        "event:list",
        "event:view",
        "client:create",
        "client:update",
        "client:delete",
        "event:create",     # To assign an event to a support contact
        "event:update",
        "event:delete",
        "event:close",
        "audit:view",
    ],
}

# Role ID to name mapping for easy lookup
ROLE_ID_TO_NAME: Dict[int, str] = {
    1: "management",
    2: "commercial", 
    3: "support"
}

def has_permission(access_token: str, required_permission: str) -> bool:
    """
    Check if the user has the required permission based on their role.
    
    Args:
        access_token: JWT access token
        required_permission: Permission to check (e.g., "client:create")
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        if not access_token:
            return False
            
        payload = verify_access_token(access_token)
        role_id = int(payload.get("role_id"))

        # Get role name from role_id
        role_name = ROLE_ID_TO_NAME.get(role_id)
        if not role_name:
            return False

        # Check if role has the required permission
        role_permissions = DEFAULT_ROLE_PERMISSIONS.get(role_name)
        return required_permission in role_permissions

    except Exception as e:
        print(f"Error checking permission: {e}")
        raise

def require_permission(permission: str):
    """
    Decorator to require specific permission for function execution.

    Args:
        permission: Required permission (e.g., "client:create")
    """
    def decorator(func):
        def wrapper(access_token: str, *args, **kwargs):
            if not access_token:
                view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
                return

            if not has_permission(access_token, permission):
                view.wrong_message(
                    f"OPERATION DENIED: You don't have permission to "
                    f"{permission.replace(':', ' ').replace('_', ' ')}."
                )
                return

            return func(access_token, *args, **kwargs)
        return wrapper
    return decorator


