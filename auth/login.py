import getpass
from datetime import datetime
import os

from db.config import Session
from crm.models import User
from auth.jwt.generate_token import generate_token
from exceptions import InvalidUsernameError, InvalidPasswordError
from auth.hashing import verify_password
from crm.views.views import MainView


view = MainView()


def login(username: str, password: str | None = None) -> tuple[str, str, datetime, bytes]:
    """
    Authenticate a user and return access and refresh tokens.

    Returns (access_token, raw_refresh, refresh_expiration, refresh_hash).
    """

    if not username:
        username = view.get_username().strip()
    if not password:
        password = getpass.getpass()
    
    
    with Session() as session:
        user = session.query(User).filter(User.username==username).one_or_none()
        if not user:
            view.wrong_message("UNKNOWN USERNAME")
            return

        if not verify_password(password, user.password_hash):
            view.wrong_message("WRONG PASSWORD")
            return

        access_token, raw_refresh, refresh_exp, refresh_hash = generate_token(
            user.id, user.role_id
        )
        view.success_message(f"Login successful.\nConnected as {user.username}")
        view.display_login(access_token, raw_refresh, refresh_exp)
        user.refresh_token_hash = refresh_hash.decode("utf-8")
        os.environ["ACCESS_TOKEN"] = access_token
        session.commit()
        return access_token, raw_refresh, refresh_exp, refresh_hash
