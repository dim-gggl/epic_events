import json
import os
import tempfile
from datetime import UTC, datetime
from typing import Any

from src.crm.views.views import view
from src.settings import TEMP_FILE_PATH

# If not assigned, TEMP_FILE_PATH is set to None. In this case,
# the temporary file is created in the system folder.
_auth_location: str | None = TEMP_FILE_PATH


def _get_auth_location() -> str:
    """Get or create the temporary token file path."""
    global _auth_location
    if not _auth_location:
        temp_dir = tempfile.gettempdir()
        _auth_location = os.path.join(temp_dir,
                                      'epic_events_session.jwt')
    return _auth_location


def store_token(access_token: str,
                refresh_token: str,
                refresh_expiry: datetime,
                user_id: int,
                role_id: int) -> None:
    """
    Store JWT tokens and user info in a temporary file.
    
    Args:
        access_token: JWT access token
        refresh_token: Raw refresh token
        refresh_expiry: Refresh token expiration datetime
        user_id: User ID
        role_id: User role ID
    """
    token_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'refresh_expiry': refresh_expiry.isoformat(),
        'user_id': user_id,
        'role_id': role_id,
        'stored_at': datetime.now(UTC).isoformat()
    }

    try:
        token_file = _get_auth_location()
        with open(token_file, 'w') as f:
            json.dump(token_data, f, ensure_ascii=True, indent=4)
        # Set restrictive file permissions (owner only)
        os.chmod(token_file, 0o700)
        return True

    except Exception as e:
        view.wrong_message(
            f"Failed to store authentication tokens: {str(e)}"
        )
        return False


def get_stored_token() -> dict[str, Any] | None:
    """
    Retrieve stored token data from temporary file.
    
    Returns:
        Dict containing token data or None if no valid token found
    """
    token_file_path = _get_auth_location()
    if not os.path.exists(token_file_path):
        return None

    try:
        with open(token_file_path) as f:
            token_data = json.load(f)
        if not token_data:
            # File is empty, treat as no token
            cleanup_token_file()
            return None
        return token_data
    except json.JSONDecodeError as e:
        view.wrong_message(f"Decode error: {e}")
        cleanup_token_file()
        return None
    except Exception as e:
        view.wrong_message(
            f"Failed to read authentication tokens: {str(e)}")
        return None

def get_access_token() -> str | None:
    """
    Get the stored access token.
    
    Returns:
        Access token string or None if not available
    """
    token_data = get_stored_token()
    if token_data:
        return token_data.get('access_token')
    return

def get_user_info_from_token() -> dict[str, Any] | None:
    """
    Get stored user information.
    
    Returns:
        Dict with user_id and role_id or None if not available
    """
    token_data = get_stored_token()
    if token_data:
        return {
            'user_id': token_data.get('user_id'),
            'role_id': token_data.get('role_id')
        }
    return None


def cleanup_token_file() -> None:
    """Remove the temporary token file."""
    token_file_path = _get_auth_location()
    if os.path.exists(token_file_path):
        os.remove(token_file_path)
    else:
        view.display_message("No token stored in the file")


def update_access_token(new_access_token: str) -> None:
    """
    Update only the access token in the stored token data.
    
    Args:
        new_access_token: New JWT access token
    """
    token_data = get_stored_token()
    if token_data:
        token_data['access_token'] = new_access_token
        token_data['stored_at'] = datetime.now(UTC).isoformat()
        # Ensure datetime fields are serialized correctly
        if isinstance(token_data.get('refresh_expiry'), datetime):
            token_data['refresh_expiry'] = token_data['refresh_expiry'].isoformat()
        if isinstance(token_data.get('stored_at'), datetime):
            token_data['stored_at'] = token_data['stored_at'].isoformat()

        try:
            token_file = _get_auth_location()
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
        except Exception as e:
            view.wrong_message(f"Failed to update access token: {str(e)}")
            raise
