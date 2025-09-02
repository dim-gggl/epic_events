"""Static role-to-permissions mapping for the CRM.

This replaces the previous JSON file at `crm/permissions.json`.
All permissions are strings and stored directly on `Role.permissions`.
"""

from __future__ import annotations

from typing import Dict, List


# Deterministic order of roles used by seeders and presentation
ORDERED_DEFAULT_ROLES: List[str] = [
    "management",
    "commercial",
    "support",
]


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


