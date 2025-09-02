from datetime import datetime
import getpass

from db.config import Session
from crm.models import User
from auth.jwt.generate_token import generate_token
from exceptions import InvalidUsernameError, InvalidPasswordError
from auth.hashing import verify_password
from crm.views.views import MainView as view

view = view()


def login(username: str, password: str | None = None) -> tuple[str, str, datetime]:
    """
    Authenticate a user and return access and refresh tokens.

    Returns (access_token, raw_refresh, refresh_expiration).
    """
    if not username or not isinstance(username, str):
        raise InvalidUsernameError()

    if not password:
        password = getpass.getpass("Password: ")

    with Session() as session:
        user: User | None = (
            session.query(User).filter(User.username == username).one_or_none()
        )
        if user is None:
            raise InvalidUsernameError()

        if not verify_password(password, user.password_hash):
            raise InvalidPasswordError()

        access_token, raw_refresh, refresh_exp, refresh_hash = generate_token(
            user.id, user.role_id
        )
        view.success_message(f"Login successful.\nConnected as {user.username}")
        view.display_login(access_token, raw_refresh, refresh_exp)
        # Persist refresh token hash for later verification
        user.refresh_token_hash = refresh_hash.decode("utf-8")
        session.commit()


        return access_token, raw_refresh, refresh_exp, refresh_hash
