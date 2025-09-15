import jwt

from src.exceptions import ExpiredTokenError, InvalidTokenError

from .config import get_all_secrets, get_secret_by_kid


def verify_access_token(token: str) -> dict:
    """
    Verify JWT access token and return payload.
    
    Args:
        token: JWT access token string
        
    Returns:
        dict: Token payload containing user information
        
    Raises:
        InvalidTokenError: If the token is invalid or missing required fields.
        ExpiredTokenError: If the token has expired.
    """
    if not token:
        raise InvalidTokenError("No token provided. Please authenticate first.")
    try:
        # Select secret based on 'kid' header if present; otherwise try all
        try:
            header = jwt.get_unverified_header(token)
            key = get_secret_by_kid(header.get("kid"))
            payload = jwt.decode(token, key=key, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            # Legacy tokens without 'kid': try known secrets in order
            last_exc = None
            for key in get_all_secrets():
                try:
                    payload = jwt.decode(token, key=key, algorithms=["HS256"])
                    break
                except jwt.InvalidTokenError as e:
                    last_exc = e
            else:
                raise last_exc or jwt.InvalidTokenError("Unable to verify token")
        if 'sub' not in payload or 'role_id' not in payload:
            raise InvalidTokenError("Token missing required fields.")
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ExpiredTokenError(f"Token has expired: {e}")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {e}")
    except Exception as e:
        raise InvalidTokenError(f"Token verification failed: {e}")
