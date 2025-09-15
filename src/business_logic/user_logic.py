
from src.auth.hashing import hash_password
from src.auth.permissions import (
    get_user_id_and_role_from_token,
    has_permission,
    has_permission_for_user,
    login_required,
    require_permission,
)
from src.crm.models import User
from src.data_access.config import Session
from src.data_access.repository import user_repository


class UserLogic:
    @require_permission("user:create")
    def create_user(self, access_token: str, user_data: dict) -> User:
        with Session() as session:
            user_data["password_hash"] = hash_password(user_data["password"])
            del user_data["password"]
            user = user_repository.create(user_data, session)
            session.commit()
            session.refresh(user)
            return user

    @require_permission("user:list")
    def get_users(self, access_token: str) -> list[User]:
        with Session() as session:
            return user_repository.get_all(session)

    @require_permission("user:view")
    def get_user_by_id(self, access_token: str, user_id: int) -> User | None:
        with Session() as session:
            user = user_repository.get_by_id(user_id, session)
            if user:
                # Load relationships to avoid lazy loading issues
                _ = user.managed_clients
                _ = user.managed_contracts
                _ = user.supported_events
            return user

    @login_required
    def update_user(self, access_token: str, user_id: int, user_data: dict) -> User | None:
        with Session() as session:
            user = user_repository.get_by_id(user_id, session)
            if not user:
                return None

            subject_user_id, _ = get_user_id_and_role_from_token(access_token)
            # Allow if role has global permission or if policy authorizes (self/any)
            if not (has_permission(access_token, "user:update") or
                    has_permission_for_user(access_token, "update", user, subject_user_id)):
                raise PermissionError("You don't have permission to update this user.")

            updated_user = user_repository.update(user_id, user_data, session)
            session.commit()
            if updated_user:
                session.refresh(updated_user)
            return updated_user

    @require_permission("user:delete")
    def delete_user(self, access_token: str, current_user_id: int, user_id_to_delete: int) -> bool:
        with Session() as session:
            if current_user_id == user_id_to_delete:
                raise ValueError("You cannot delete your own account.")

            user = user_repository.get_by_id(user_id_to_delete, session)
            if not user:
                return False

            # Business rule: cannot delete user with associated records
            if user.managed_clients or user.managed_contracts or user.supported_events:
                raise ValueError("Cannot delete user with associated records.")

            deleted = user_repository.delete(user_id_to_delete, session)
            if deleted:
                session.commit()
            return deleted

user_logic = UserLogic()
