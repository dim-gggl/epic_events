import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta, timezone

from .config import (
    ACCESS_TOKEN_LIFETIME_MINUTES,
    REFRESH_TOKEN_LIFETIME_DAYS,
    SECRET_KEY
)
from db.config import Session
from crm.models import User
from crm.views.views import MainView
from auth.jwt.token_storage import update_access_token
from exceptions import InvalidTokenError, ExpiredTokenError

view = MainView()


def refresh_access_token(user_id: int, 
                        provided_refresh: str) -> \
                        tuple[str, str, datetime, bytes]:
    """
    Refresh the access token of a user.
    
    Args:
        user_id: ID of the user requesting token refresh
        provided_refresh: Raw refresh token provided by user
        
    Returns:
        A tuple containing:
        - New JWT access token
        - New raw refresh token
        - New expiration datetime
        - New hashed refresh token
        
    Raises:
        InvalidTokenError: If user not found or refresh token invalid
        ExpiredTokenError: If refresh token has expired
    """
    with Session() as session:
        # Get user with stored refresh token data
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            raise InvalidTokenError("Invalid user ID")
            
        if not user.refresh_token_hash or not user.refresh_token_expiry:
            raise InvalidTokenError("No refresh token saved for this user")

        # Check if the refresh token has expired
        if datetime.now(timezone.utc) > user.refresh_token_expiry:
            raise ExpiredTokenError("Refresh token has expired")

        # Check if the provided refresh token matches the stored hash
        stored_hash_bytes = user.refresh_token_hash.encode('utf-8')
        if not bcrypt.checkpw(provided_refresh.encode('utf-8'), stored_hash_bytes):
            raise InvalidTokenError("Invalid refresh token")

        # At this point, the refresh token is authenticated and valid
        # Generate a new access token
        new_exp = datetime.now(timezone.utc) + \
            timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
        new_payload = {
            "sub": str(user_id), 
            "role_id": str(user.role_id),
            "exp": new_exp
        }
        new_access = jwt.encode(new_payload, SECRET_KEY, algorithm="HS256")

        # Rotate the refresh token for enhanced security
        new_refresh_raw = secrets.token_urlsafe(32)
        new_refresh_hash = bcrypt.hashpw(new_refresh_raw.encode('utf-8'), 
                                        bcrypt.gensalt())

        # Compute the expiration date of the refresh token
        new_refresh_exp = datetime.now(timezone.utc) + \
            timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)

        # Update the database with new refresh token
        user.refresh_token_hash = new_refresh_hash.decode('utf-8')
        user.refresh_token_expiry = new_refresh_exp
        session.commit()
        
        # Update the stored access token in temporary file
        try:
            update_access_token(new_access)
        except Exception:
            # If updating token storage fails, log but don't fail the refresh
            view.warning_message("Token refreshed but storage update failed")
        
        view.success_message("Access token successfully refreshed")
        return new_access, new_refresh_raw, new_refresh_exp, new_refresh_hash
