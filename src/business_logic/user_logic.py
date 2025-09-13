from src.data_access.repository import user_repository
from src.data_access.config import Session
from src.crm.models import User
from src.auth.permissions import has_permission_for_user, require_permission
from src.auth.hashing import hash_password
from typing import List, Optional

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
    def get_users(self, access_token: str) -> List[User]:
        with Session() as session:
            return user_repository.get_all(session)

    @require_permission("user:view")
    def get_user_by_id(self, access_token: str, user_id: int) -> Optional[User]:
        with Session() as session:
            user = user_repository.get_by_id(user_id, session)
            if user:
                # Load relationships to avoid lazy loading issues
                _ = user.managed_clients
                _ = user.managed_contracts
                _ = user.supported_events
            return user

    @require_permission("user:update")
    def update_user(self, access_token: str, user_id: int, user_data: dict) -> Optional[User]:
        with Session() as session:
            user = user_repository.get_by_id(user_id, session)
            if not user:
                return None

            if not has_permission_for_user(access_token, "update", user, user_id):
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
