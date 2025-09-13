import getpass
from datetime import datetime

from src.data_access.config import Session
from src.crm.models import User
from src.auth.jwt.generate_token import generate_token
from src.auth.jwt.token_storage import store_token
from src.auth.hashing import verify_password
from src.views.views import MainView
from src.sentry.observability import log_authentication_event

view = MainView()

def login(username: str, password: str | None = None) -> tuple[str, str, datetime, bytes]:
    """
    Authenticate a user and return access and refresh tokens.

    Returns (access_token, raw_refresh, refresh_expiration, refresh_hash).
    Raises InvalidUsernameError or InvalidPasswordError on failure.
    """
    if not username:
        username = view.get_username().strip()
    if not password:
        password = getpass.getpass()
        
    with Session() as session:
        user = session.query(User).filter(User.username==username).one_or_none()
        if not user:
            log_authentication_event("login_failed", success=False, context={"reason": "unknown_username", "username": username})
            view.wrong_message("Unknown username.")
            return
        
        if not verify_password(password, user.password_hash):
            log_authentication_event("login_failed", success=False, context={"reason": "wrong_password", "user_id": user.id})
            view.wrong_message("Wrong password.")
            return
            
        access_token, raw_refresh, refresh_exp, refresh_hash = generate_token(user.id, user.role_id)
        user.refresh_token_hash = refresh_hash.decode("utf-8")
        session.commit()
        
        store_token(access_token, raw_refresh, refresh_exp, user.id, user.role_id)
        log_authentication_event("login_success", success=True, context={"user_id": user.id})
        
        view.success_message(f"Login successful. Connected as {user.username}")
        view.display_login(access_token, raw_refresh, refresh_exp)
        
        return access_token, raw_refresh, refresh_exp, refresh_hash
