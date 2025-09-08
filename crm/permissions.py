from __future__ import annotations

from typing import Dict, List
from crm.views.views import MainView
from auth.jwt.verify_token import verify_access_token


ORDERED_DEFAULT_ROLES: List[str] = [
    "management",
    "commercial",
    "support",
]

view = MainView()

def login_required(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not access_token or not access_token.strip():
            view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def commercial_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not access_token or not access_token.strip():
            view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
            return
        if not int(verify_access_token(access_token)["role_id"]) == 2:
            view.wrong_message("OPERATION DENIED: This action is only available to commercial users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def management_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not access_token or not access_token.strip():
            view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
            return
        if not verify_access_token(access_token)["role_id"] == 1:
            view.wrong_message("OPERATION DENIED: This action is only available to management users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def support_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not access_token or not access_token.strip():
            view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
            return
        if not verify_access_token(access_token)["role_id"] == 3:
            view.wrong_message("OPERATION DENIED: This action is only available to support users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper
            
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "support": [
        # Read access to all main resources  
        "client:list:any",
        "client:view:any",
        "contract:list:any", 
        "contract:view:any",
        "event:list:any",
        "event:view:any",
        # Original support permissions
        "event:update:assigned",
        "event:comment:assigned",
    ],
    "commercial": [
        # Read access to all main resources
        "client:list:any",
        "client:view:any", 
        "contract:list:any",
        "contract:view:any",
        "event:list:any",
        "event:view:any",
        # Original commercial permissions
        "client:create",
        "client:update:own",
        "contract:update:own",
        "event:create:own_client",
        "event:comment:own_client",
    ],
    "management": [
        "user:list:any",
        "user:view:any",
        "user:create",
        "user:update:any",
        "user:delete",
        "role:list:any",
        "role:view:any",
        "role:assign",
        "client:list:any",
        "client:view:any",
        "contract:list:any",
        "contract:view:any",
        "contract:create:any",
        "contract:update:any",
        "contract:delete",
        "event:list:any",
        "event:view:any",
        "client:create",
        "client:update:any",
        "client:delete",
        "event:create:any",     # To assign an event to a support contact
        "event:update:any",
        "event:delete",
        "event:close:any",
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
        role_id = int(payload.get("role_id", 0))

        # Get role name from role_id
        role_name = ROLE_ID_TO_NAME.get(role_id)
        if not role_name:
            return False

        # Check if role has the required permission
        role_permissions = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        return required_permission in role_permissions

    except Exception:
        return False

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
                view.wrong_message(f"OPERATION DENIED: You don't have permission to {permission.replace(':', ' ').replace('_', ' ')}.")
                return

            return func(access_token, *args, **kwargs)
        return wrapper
    return decorator


