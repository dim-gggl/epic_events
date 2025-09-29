from typing import Optional

import jwt

from src.auth.jwt.config import get_all_secrets, get_secret_by_kid
from src.exceptions import ExpiredTokenError, InvalidTokenError


def _decode_with_secret(token: str, secret: str) -> dict:
    """Decode the JWT using the provided secret, enforcing required claims."""
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    if 'sub' not in payload or 'role_id' not in payload:
        raise InvalidTokenError("Token missing required fields.")
    return payload


def verify_access_token(token: str) -> dict:
    """Verify JWT access token and return payload, supporting key rotation."""
    if not token:
        raise InvalidTokenError(
            "Invalid token: no token provided. Please authenticate first."
        )

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(f"Invalid token header: {exc}") from exc

    kid = header.get('kid') if isinstance(header, dict) else None

    secrets_to_try = [get_secret_by_kid(kid)] if kid else get_all_secrets()

    last_error: Optional[Exception] = None
    for secret in secrets_to_try:
        try:
            return _decode_with_secret(token, secret)
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredTokenError(f"Token has expired: {exc}") from exc
        except jwt.InvalidTokenError as exc:  # signature mismatch, malformed, etc.
            last_error = exc
            continue

    error_message = "Token verification failed."
    if last_error:
        error_message = f"Token verification failed: {last_error}"
    raise InvalidTokenError(error_message) from last_error
