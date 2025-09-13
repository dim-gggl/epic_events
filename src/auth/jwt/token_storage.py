import os
import tempfile
import json
from datetime import datetime
from typing import Optional, Dict, Any

from src.views.views import MainView

view = MainView()

_auth_location: Optional[str] = None


def _get_auth_location() -> str:
    """Get or create the temporary token file path."""
    global _auth_location
    if _auth_location is None:
        # Use a fixed temporary file path that persists across process invocations
        temp_dir = tempfile.gettempdir()
        _auth_location = os.path.join(temp_dir, 'epic_events_session.jwt')
    return _auth_location


def store_token(access_token: str, refresh_token: str, refresh_expiry: datetime, user_id: int, role_id: int) -> None:
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
        'stored_at': datetime.utcnow().isoformat()
    }
    
    try:
        token_file = _get_auth_location()
        with open(token_file, 'w') as f:
            json.dump(token_data, f)
        # Set restrictive file permissions (owner only)
        os.chmod(token_file, 0o600)
    except Exception as e:
        view.wrong_message(f"Failed to store authentication tokens: {str(e)}")
        raise


def get_stored_token() -> Optional[Dict[str, Any]]:
    """
    Retrieve stored token data from temporary file.
    
    Returns:
        Dict containing token data or None if no valid token found
    """
    token_file_path = _get_auth_location()
    if not os.path.exists(token_file_path):
        os.makedirs(os.path.dirname(token_file_path), exist_ok=True)            
        return None
    
    try:
        with open(token_file_path, 'r') as f:
            content = f.read().strip()
            if not content:
                # File is empty, treat as no token
                cleanup_token_file()
                return None
            token_data = json.loads(content)
        
        # Convert refresh_expiry back to datetime
        if 'refresh_expiry' in token_data:
            token_data['refresh_expiry'] = datetime.fromisoformat(token_data['refresh_expiry'])
        if 'stored_at' in token_data:
            token_data['stored_at'] = datetime.fromisoformat(token_data['stored_at'])
            
        return token_data

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        view.wrong_message(f"Invalid token file format. \n{e}")
        cleanup_token_file()
        return None

    except Exception as e:
        view.wrong_message(f"Failed to read authentication tokens: {str(e)}")
        raise


def get_access_token() -> Optional[str]:
    """
    Get the stored access token.
    
    Returns:
        Access token string or None if not available
    """
    token_data = get_stored_token()
    return token_data.get('access_token') if token_data else None


def get_user_info() -> Optional[Dict[str, Any]]:
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
        token_data['stored_at'] = datetime.utcnow().isoformat()
        
        try:
            token_file = _get_auth_location()
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
        except Exception as e:
            view.wrong_message(f"Failed to update access token: {str(e)}")
            raise
