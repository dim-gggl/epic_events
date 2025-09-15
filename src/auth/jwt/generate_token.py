import datetime
import secrets

import bcrypt
import jwt

from .config import (
    ACCESS_TOKEN_LIFETIME_MINUTES,
    REFRESH_TOKEN_LIFETIME_DAYS,
    get_current_kid,
    get_secret_by_kid,
)


def generate_token(
    user_id: int,
    user_role_id: int,
) -> tuple[str, str, datetime.datetime, bytes]:
    """
    Generate a new access token and refresh token for a user.

    Args:
        user_id: The id of the user.
        user_role_id: The role id of the user.

    Returns:
        A tuple containing:
        - access_token: JWT access token
        - raw_refresh: Raw refresh token (to send to user)
        - refresh_exp: Expiration datetime of refresh token
        - refresh_hash: Hashed refresh token (to store in database)
    """
    secret = get_secret_by_kid(get_current_kid())

    expiration = datetime.datetime.now(datetime.UTC) + \
        datetime.timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
    access_payload = {
        "sub": str(user_id),            # We use the user id as the subject
        "role_id": str(user_role_id),   # We also include the role id
        "exp": expiration               # We set the expiration date
    }

    # Generate the access token and the raw refresh token
    access_token = jwt.encode(
        access_payload,
        secret,
        algorithm="HS256",
        headers={"kid": get_current_kid()},
    )
    raw_refresh = secrets.token_urlsafe(32)

    # Hash the refresh token
    refresh_hash = bcrypt.hashpw(raw_refresh.encode('utf-8'),
                                 bcrypt.gensalt())

    # Compute the expiration date of the refresh token
    refresh_exp = datetime.datetime.now(datetime.UTC) + \
        datetime.timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    return access_token, raw_refresh, refresh_exp, refresh_hash
