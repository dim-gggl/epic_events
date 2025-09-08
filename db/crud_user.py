from auth.jwt.verify_token import verify_access_token
from crm.models import User
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import require_permission, login_required, has_permission
from db.config import Session
from auth.register import create_user as register_user
from sqlalchemy import select

view = MainView()
controller = MainController()

@require_permission("user:create")
def create_user(access_token: str, 
                username: str = None, 
                full_name: str = None, 
                email: str = None, 
                password: str = None, 
                role_id: int = None):
    """
    Create a new user. Only management can create users.
    Uses the existing create_user function from auth/register.py
    """
    # Use existing create_user function from auth.register
    register_user(
        access_token, username, full_name, email, password, role_id
    )

@require_permission("user:list:any")
def list_users(access_token: str):
    """List all users. Only management can list users."""
    with Session() as session:
        users = session.scalars(select(User)).all()
        view.display_users(users)

@login_required
def view_user(access_token: str, user_id: int):
    """View a specific user."""
    with Session() as session:
        current_user_id = int(verify_access_token(access_token)["sub"])
        user = session.scalars(
            select(User).filter(User.id == user_id)
        ).one_or_none()
        
        if not user:
            view.wrong_message("OPERATION DENIED: User not found.")
            return
            
        # Check permissions - management can view any user, others can only view themselves
        if not (has_permission(access_token, "user:view:any") or current_user_id == user_id):
            view.wrong_message("OPERATION DENIED: You can only view your own profile.")
            return
            
        view.display_user(user)

@require_permission("user:update:any")
def update_user(access_token: str, user_id: int, **kwargs):
    """Update a user. Only management can update users."""
    with Session() as session:
        user = session.scalars(
            select(User).filter(User.id == user_id)
        ).one_or_none()
        
        if not user:
            view.wrong_message("OPERATION DENIED: User not found.")
            return
            
        # Get updated data if not provided via kwargs
        if not any(kwargs.values()):
            # Prompt for each field
            username = kwargs.get('username', view.get_username())
            full_name = kwargs.get('full_name', view.get_full_name())
            email = kwargs.get('email', view.get_email())
            role_id = kwargs.get('role_id', int(view.get_role_id()))
            
            # Update fields
            user.username = username if username else user.username
            user.full_name = full_name if full_name else user.full_name
            user.email = email if email else user.email
            user.role_id = role_id if role_id else user.role_id
        else:
            # Update with provided values
            for key, value in kwargs.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
                    
        session.commit()
        view.success_message(f"User '{user.username}' has been updated successfully.")

@require_permission("user:delete")
def delete_user(access_token: str, user_id: int):
    """Delete a user. Only management can delete users."""
    with Session() as session:
        current_user_id = int(verify_access_token(access_token)["sub"])
        
        # Prevent self-deletion
        if current_user_id == user_id:
            view.wrong_message("OPERATION DENIED: You cannot delete your own account.")
            return
            
        user = session.scalars(select(User).filter(User.id == user_id)).one_or_none()
        
        if not user:
            view.wrong_message("OPERATION DENIED: User not found.")
            return
            
        # Check if user has associated records that would prevent deletion
        if user.managed_clients or user.managed_contracts or user.supported_events:
            view.wrong_message("OPERATION DENIED: Cannot delete user with associated records.")
            return
            
        session.delete(user)
        session.commit()
        view.success_message(f"User '{user.username}' (ID: {user_id}) has been deleted successfully.")
