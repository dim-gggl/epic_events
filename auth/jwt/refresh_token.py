import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta, timezone

from .config import (
    cur,
    conn,
    ACCESS_TOKEN_LIFETIME_MINUTES,
    REFRESH_TOKEN_LIFETIME_DAYS,
    SECRET_KEY
)
from .verify_token import verify_access_token
from exceptions import (
    InvalidTokenError, 
    OperationDeniedError, 
    InvalidUserIDError, 
    NoRefreshTokenSavedError, 
    ExpiredTokenError
)


def refresh_access_token(user_id: int, 
                        provided_refresh: str) -> \
                            tuple[str, str, datetime, bytes]:
    """
    Refresh the access token of a user.
    
    Returns:
        A tuple containing:
        - New JWT access token
        - New raw refresh token
        - New expiration datetime
        - New hashed refresh token
    """
    # Get the stored hash and expiration date for the user
    cur.execute(
        "SELECT refresh_token_hash, refresh_token_expiry "
        "FROM users WHERE id = %s", (user_id,)
    )
    result = cur.fetchone()
    if result is None:
        raise InvalidUserIDError()
    stored_hash, stored_exp = result
    if stored_hash is None or stored_exp is None:
        raise NoRefreshTokenSavedError()

    # Check if the refresh token has expired
    if datetime.now(timezone.utc) > stored_exp:
        raise ExpiredTokenError()

    # Check if the provided refresh token corresponds to the stored hash
    stored_hash_bytes = stored_hash.encode('utf-8')
    if not bcrypt.checkpw(provided_refresh.encode('utf-8'), 
                        stored_hash_bytes):
        raise InvalidTokenError()

    # At this point, the refresh token is authenticated and valid
    # Generate a new access token
    new_exp = datetime.now(timezone.utc) + \
        timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
    new_payload = {"sub": str(user_id), "exp": new_exp}
    new_access = jwt.encode(new_payload, SECRET_KEY, algorithm="HS256")

    # Optional: rotate the refresh token
    new_refresh_raw = secrets.token_urlsafe(32)
    new_refresh_hash = bcrypt.hashpw(new_refresh_raw.encode('utf-8'), 
                                    bcrypt.gensalt())

    # Compute the expiration date of the refresh token
    new_refresh_exp = datetime.now(timezone.utc) + \
        timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)

    # Update the database
    cur.execute(
        "UPDATE users SET refresh_token_hash = %s, refresh_token_expiry = %s "
        "WHERE id = %s",
        (new_refresh_hash.decode('utf-8'), new_refresh_exp, user_id)
    )
    conn.commit()
    return new_access, new_refresh_raw, new_refresh_exp, new_refresh_hash
