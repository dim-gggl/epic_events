import jwt
from src.auth.utils import get_secret_key
from src.exceptions import InvalidTokenError, ExpiredTokenError

SECRET_KEY = get_secret_key()

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
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
        if 'sub' not in payload or 'role_id' not in payload:
            raise InvalidTokenError("Token missing required fields.")
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ExpiredTokenError(f"Token has expired: {e}")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {e}")
    except Exception as e:
        raise InvalidTokenError(f"Token verification failed: {e}")

