import datetime

import bcrypt

from src.crm.models import User
from src.data_access.config import Session
from src.views.views import MainView

from .generate_token import generate_token
from .token_storage import (
    get_stored_token,
    get_user_info_from_token,
    store_token,
)

view = MainView()


def refresh_tokens() -> tuple[str, str, datetime.datetime] | None:
    """
    Rotate and refresh tokens using the stored refresh token.

    Steps:
    - Load stored token data (access, refresh, expiry, user info).
    - Ensure refresh token not expired.
    - Fetch user and compare stored refresh hash (DB) with provided refresh.
    - Issue new access + refresh; replace DB hash; persist to secure storage.

    Returns: (new_access_token, new_raw_refresh, new_refresh_expiry)
    """
    tok = get_stored_token()
    if not tok:
        view.wrong_message("No stored session. Please login first.")
        return None

    user_info = get_user_info_from_token()
    if not user_info:
        view.wrong_message("Missing user info in session. Please login again.")
        return None

    refresh_raw = tok.get("refresh_token")
    refresh_exp = tok.get("refresh_expiry")
    if not refresh_raw or not refresh_exp:
        view.wrong_message("Refresh token unavailable. Please login again.")
        return None

    now = datetime.datetime.now(datetime.UTC)
    if isinstance(refresh_exp, datetime.datetime) and now >= refresh_exp:
        view.wrong_message("Refresh token expired. Please login again.")
        return None

    user_id = int(user_info["user_id"])  # type: ignore

    with Session() as session:
        user = session.get(User, user_id)
        if not user or not user.refresh_token_hash:
            view.wrong_message("Cannot validate refresh token. Please login again.")
            return None

        if not bcrypt.checkpw(refresh_raw.encode("utf-8"),
                              user.refresh_token_hash.encode("utf-8")):
            view.wrong_message("Invalid refresh token. Please login again.")
            return None

        # Rotate: generate a new pair and replace stored hash
        access_token, new_raw_refresh, new_refresh_exp, new_refresh_hash = generate_token(user.id, user.role_id)
        user.refresh_token_hash = new_refresh_hash.decode("utf-8")
        session.commit()

        # Persist session file with new values
        store_token(access_token, new_raw_refresh, new_refresh_exp, user.id, user.role_id)
        view.success_message("Session refreshed and rotated successfully.")
        return access_token, new_raw_refresh, new_refresh_exp
