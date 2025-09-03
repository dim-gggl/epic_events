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
        if not access_token:
            view.wrong_message("OPERATION DENIED: You are not authorized to access this resource.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def commercial_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not int(verify_access_token(access_token)["role_id"]) == 2:
            view.wrong_message("OPERATION DENIED: This action is only available to commercial users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def management_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not verify_access_token(access_token)["role_id"] == 1:
            view.wrong_message("OPERATION DENIED: This action is only available to management users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper

def support_exclusive(func):
    def wrapper(access_token: str, *args, **kwargs):
        if not verify_access_token(access_token)["role_id"] == 3:
            view.wrong_message("OPERATION DENIED: This action is only available to support users.")
            return
        else:
            return func(access_token, *args, **kwargs)
    return wrapper
            
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "support": [
        "client:view:assigned",
        "contract:view:assigned",
        "event:list:assigned",
        "event:view:assigned",
        "event:update:assigned",
        "event:comment:assigned",
    ],
    "commercial": [
        "client:list:own",
        "client:view:own",
        "client:create",
        "client:update:own",
        "contract:list:own",
        "contract:view:own",
        "contract:create:own_client",
        "contract:update:own",
        "event:list:own_client",
        "event:view:own_client",
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
        "event:list:any",
        "event:view:any",
        "client:create",
        "client:update:any",
        "client:delete",
        "contract:create:any",
        "contract:update:any",
        "contract:delete",
        "event:create:any",
        "event:update:any",
        "event:delete",
        "contract:sign",
        "event:assign",
        "event:close:any",
        "audit:view",
    ],
}


