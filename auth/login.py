import jwt
import bcrypt
from datetime import datetime

from .jwt.generate_token import generate_token
from .jwt.config import cur, conn
from exceptions import InvalidUsernameError, InvalidPasswordError
from .hashing import verify_password



def login(username: str, password: str) -> tuple[str, str, datetime]:
    """
    Login a user and return the access token and the refresh token.

    Args:
        username: The username of the user.
        password: The password of the user.

    Returns:
        A tuple containing the access token, the raw refresh token, and the 
        expiration date of the refresh token.
    """

    # Get the user by the username
    cur.execute(
        "SELECT id, password_hash, role_id FROM users WHERE username = %s", 
        (username,)
    )
    result = cur.fetchone()
    if result is None:
        raise InvalidUsernameError()
    user_id, stored_hash, user_role_id = result
    
    # Check the password
    if not verify_password(password, stored_hash):
        raise InvalidPasswordError()

    # Password ok -> generate the access token
    access_token, raw_refresh, refresh_exp, refresh_hash = generate_token(user_id, user_role_id)

    cur.execute(
        "UPDATE users SET refresh_token_hash = %s, refresh_token_expiry = %s "
        "WHERE id = %s",
        (refresh_hash.decode('utf-8'), refresh_exp, user_id)
    )
    conn.commit()

    # Return the two tokens to the client and the expiration date 
    # of the refresh token
    return access_token, raw_refresh, refresh_exp
