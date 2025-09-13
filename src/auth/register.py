from src.business_logic.user_logic import user_logic
from src.auth.permissions import require_permission

@require_permission("user:create")
def register_user(access_token: str, username: str, full_name: str, email: str, password: str, role_id: int):
    """
    Register a new user. This is a wrapper around user_logic.create_user.
    """
    user_data = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "password": password,
        "role_id": role_id
    }
    user_logic.create_user(access_token, user_data)
