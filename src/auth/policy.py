
from src.auth.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    ROLE_ID_TO_NAME,
    get_user_id_and_role_from_token,
)
from src.crm.models import Role
from src.data_access.config import Session
from src.auth.permissions import _permissions_from_db as _get_role_permissions_from_db



def get_effective_permissions(role_id: int) -> set[str]:
    perms = _get_role_permissions_from_db(role_id)
    if perms:
        return perms
    # Fallback to defaults by role name
    role_name = ROLE_ID_TO_NAME.get(role_id)
    return set(DEFAULT_ROLE_PERMISSIONS.get(role_name, []))


def enforce_any_or_own(access_token: str, resource: str, action: str, owner_user_id: int) -> None:
    """Allow if role has resource:action (any) or resource:action:own and owns the resource."""
    subject_user_id, role_id = get_user_id_and_role_from_token(access_token)
    perms = get_effective_permissions(role_id)
    any_code = f"{resource}:{action}"
    own_code = f"{resource}:{action}:own"
    if any_code in perms:
        return
    if own_code in perms and owner_user_id == subject_user_id:
        return
    raise PermissionError(
        f"You don't have permission to {action} {resource} (own/any mismatch)."
    )


def enforce_any_or_assigned(access_token: str, resource: str, action: str, assigned_user_id: int | None) -> None:
    """Allow if role has resource:action (any) or resource:action:assigned with assignment match."""
    subject_user_id, role_id = get_user_id_and_role_from_token(access_token)
    perms = get_effective_permissions(role_id)
    any_code = f"{resource}:{action}"
    assigned_code = f"{resource}:{action}:assigned"
    if any_code in perms:
        return
    if assigned_code in perms and assigned_user_id == subject_user_id:
        return
    raise PermissionError(
        f"You don't have permission to {action} {resource} (assigned/any mismatch)."
    )


def can_create_event_for_contract(access_token: str, contract_commercial_id: int) -> bool:
    subject_user_id, role_id = get_user_id_and_role_from_token(access_token)
    perms = get_effective_permissions(role_id)
    if "event:create" in perms:
        return True
    if "event:create:own_client" in perms and contract_commercial_id == subject_user_id:
        return True
    return False

