
from sqlalchemy.orm import joinedload

from src.auth.permissions import require_permission
from src.crm.models import PermissionModel, Role
from src.data_access.config import Session


class RoleLogic:
    @require_permission("role:list")
    def list_roles(self, access_token: str) -> list[Role]:
        with Session() as session:
            return (
                session
                .query(Role)
                .options(joinedload(Role.permissions_rel))
                .all()
            )

    @require_permission("role:view")
    def view_role(self, access_token: str, role_id: int) -> Role | None:
        with Session() as session:
            return (
                session
                .query(Role)
                .options(joinedload(Role.permissions_rel))
                .filter(Role.id == role_id)
                .first()
            )

    @require_permission("role:assign")
    def grant_permission(self,
                        access_token: str,
                        role_id: int,
                        permission_name: str) -> Role | None:
        with Session() as session:
            role = (
                session
                .query(Role)
                .options(joinedload(Role.permissions_rel))
                .filter(Role.id == role_id)
                .first()
            )
            if not role:
                return None

            perm = (
                session
                .query(PermissionModel)
                .filter(PermissionModel.name == permission_name)
                .first()
            )
            if not perm:
                perm = PermissionModel(name=permission_name)
                session.add(perm)
                session.flush()

            if perm not in role.permissions_rel:
                role.permissions_rel.append(perm)
            if permission_name not in (role.permissions or []):
                # Keep ARRAY mirror in sync for compatibility
                role.permissions = list(role.permissions or []) + [permission_name]

            session.commit()
            session.refresh(role)
            return role

    @require_permission("role:assign")
    def revoke_permission(self,
                          access_token: str,
                          role_id: int,
                          permission_name: str) -> Role | None:
        with Session() as session:
            role = (
                session
                .query(Role)
                .options(joinedload(Role.permissions_rel))
                .filter(Role.id == role_id)
                .first()
            )
            if not role:
                return None

            # Remove from relationship if present
            role.permissions_rel = [p for p in role.permissions_rel if p.name != permission_name]
            # Remove from ARRAY mirror
            if role.permissions:
                role.permissions = [p for p in role.permissions if p != permission_name]

            session.commit()
            session.refresh(role)
            return role

    @require_permission("role:view")
    def list_all_permission_names(self, access_token: str) -> list[str]:
        with Session() as session:
            return [
                p.name for p in session.query(
                    PermissionModel).order_by(
                        PermissionModel.name.asc()).all()
            ]


role_logic = RoleLogic()

