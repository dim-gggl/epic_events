import bcrypt

from .jwt.verify_token import verify_access_token
from db.config import Session
from crm.models import User
from exceptions import InvalidTokenError, OperationDeniedError
from crm.controllers import MainController as controller
from crm.views.views import MainView as view
from auth.jwt.verify_token import verify_access_token
from auth.hashing import hash_password

controller = controller()
view = view()

def create_user(access_token: str, 
                username: str, 
                full_name: str, 
                email: str, 
                password: str, 
                role_id: int) -> None:
    """
    Create a new user in the database.

    Args:
        access_token_payload: Decoded access token payload of the current user.
        Must contain a manager role; otherwise the operation is denied.
        username: The username of the new user.
        full_name: The full name of the new user.
        email: The email of the new user.
        password: The password of the new user.
        role_id: The role id of the new user.
    """
    access_token_payload = verify_access_token(access_token)
    if not access_token_payload:
        view.wrong_message("OPERATION DENIED: Invalid access token.")
        return

    role = access_token_payload.get("role_id")
    if int(role) != 1:
        view.wrong_message("OPERATION DENIED: You are not authorized to create a user.")
        return
        
    if not username:
        username = controller.get_username()
    if not full_name:
        full_name = controller.get_full_name()
    if not email:
        email = controller.get_email()
    if not password:
        password = controller.get_password()
    if not role_id:
        role_id = controller.get_role_id()

    # Hash password with bcrypt and keep bytes
    password_hash = hash_password(password)

    # Use SQLAlchemy ORM instead of raw SQL
    with Session() as session:
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role_id=role_id
        )
        session.add(user)
        session.commit()
    
    view.success_message(f"User '{username}' registered successfully.")
