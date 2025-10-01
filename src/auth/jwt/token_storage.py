import json
import os
import tempfile
from datetime import UTC, datetime
from typing import Any

from src.crm.views.views import view
from src.exceptions import TokenFileNotFoundError
from src.settings import TEMP_FILE_PATH


def _get_auth_location() -> str:
    """
	Return the token storage file path, defaulting 
	to system temp.
	"""
    if TEMP_FILE_PATH:
        return TEMP_FILE_PATH
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, "epic_events_session.jwt")


def store_token(access_token: str,
                refresh_token: str,
                refresh_expiry: datetime,
                user_id: int,
                role_id: int) -> bool:
    """
    Store JWT tokens and user info in a temporary file.

    Args:
        access_token: JWT access token
        refresh_token: Raw refresh token
        refresh_expiry: Refresh token expiration datetime
        user_id: User ID
        role_id: User role ID

    Returns:
        bool: True if the token bundle was stored 
		successfully, False otherwise.
    """
    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_expiry": refresh_expiry.isoformat(),
        "user_id": user_id,
        "role_id": role_id,
        "stored_at": datetime.now(UTC).isoformat()
    }

    try:
        token_file = _get_auth_location()
        directory = os.path.dirname(token_file)
        if not directory:
            os.makedirs(directory, exist_ok=True)

        with open(token_file, "w", encoding="utf-8") as file_handle:
            json.dump(token_data, file_handle, ensure_ascii=True, indent=4)

        # Set restrictive file permissions 
		# (read/write for owner and read-only
		# for group and others)
        os.chmod(token_file, 0o644)
        return True

    except Exception as exc:
        view.wrong_message(
            f"Failed to store authentication tokens: {str(exc)}"
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
        raise TokenFileNotFoundError()

    try:
        with open(token_file_path) as f:
            token_data = json.load(f)
        if not token_data:
            # File is empty, treat as no token
            cleanup_token_file()
            return None
        return token_data
    except json.JSONDecodeError as exc:
        view.wrong_message(f"Decode error: {exc}")
        cleanup_token_file()
        return None
    except Exception as exc:
        view.wrong_message(
            f"Failed to read authentication tokens: {str(exc)}")
        return None

def get_access_token() -> str | None:
    """
    Get the stored access token.
    
    Returns:
        Access token string or None if not available
    """
    try:
        token_data = get_stored_token()
        return token_data.get("access_token")
    except TokenFileNotFoundError as e:
        view.wrong_message(e)
        return None

def get_user_info_from_token() -> dict[str, Any] | None:
    """
    Get stored user information.
    
    Returns:
        Dict with user_id and role_id or None if not available
    """
    try:
        token_data = get_stored_token()
        return {
            "user_id": token_data.get("user_id"),
            "role_id": token_data.get("role_id")
        }
    except TokenFileNotFoundError as e:
        view.wrong_message(e)
        return None

def cleanup_token_file(raise_on_error: bool = False) -> None:
    """Remove the temporary token file.

    Args:
        raise_on_error: When True, re-raise file system errors so callers can
            handle them explicitly (used during logout to surface issues).
    """
    token_file_path = _get_auth_location()
    if not os.path.exists(token_file_path):
        raise TokenFileNotFoundError()

    try:
        os.remove(token_file_path)
    except OSError as exc:
        if raise_on_error:
            raise
        view.wrong_message(
            f"Could not remove authentication token file: {exc}"
        )


def update_access_token(new_access_token: str) -> None:
    """
    Update only the access token in the stored token data.
    
    Args:
        new_access_token: New JWT access token
    """
    token_data = get_stored_token()
    if token_data:
        token_data["access_token"] = new_access_token
        token_data["stored_at"] = datetime.now(UTC).isoformat()
        # Ensure datetime fields are serialized correctly
        if isinstance(token_data.get("refresh_expiry"), datetime):
            token_data["refresh_expiry"] = token_data["refresh_expiry"].isoformat()
        if isinstance(token_data.get("stored_at"), datetime):
            token_data["stored_at"] = token_data["stored_at"].isoformat()

        try:
            token_file = _get_auth_location()
            payload = json.dumps(token_data, ensure_ascii=True, indent=4)
            with open(token_file, "w", encoding="utf-8") as file_handle:
                file_handle.write(payload)
        except Exception as exc:
            view.wrong_message(f"Failed to update access token: {str(exc)}")
