from rich.console import Console

from src.auth.decorators import require_elevated_privileges
from src.auth.jwt.refresh_token import refresh_tokens
from src.auth.jwt.token_storage import get_access_token, update_access_token
from src.auth.jwt.verify_token import verify_access_token
from src.auth.login import login
from src.auth.logout import logout
from src.auth.validators import is_valid_password
from src.crm.views.helper_view import HelperView
from src.crm.views.views import MainView
from src.data_access.create_manager import init_manager as manager_create
from src.data_access.create_tables import init_db as db_create
from src.exceptions import ExpiredTokenError, InvalidTokenError
from src.settings import TEMP_FILE_PATH

console = Console()
view = MainView()
helper_view = HelperView()


class AuthController:

    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.password_hash = None
        self.temp_file = TEMP_FILE_PATH

    def _verify_token(self):
        # Getting the access token from the temp
        # file where it is stored
        token = get_access_token()
        try:
            # If token is present in the file, check
            # the information within
            payload = verify_access_token(token)
            return payload

        # Otherwise displays the caught
        # exceptions messages
        except InvalidTokenError as e:
            view.wrong_message(e)
        except ExpiredTokenError as er:
            view.wrong_message(er)

    def _prompt_password(self, confirm: bool = True):
        pwd = console.input("New password: ", password=True).strip()
        if not is_valid_password(pwd):
            helper_view.password_helper()
            return self._prompt_password()
        if confirm:
            rep = console.input("Confirm password: ", password=True).strip()
            if pwd != rep:
                helper_view.confirm_password_helper()
                rep2 = console.input("Confirm password: ", password=True).strip()
                if pwd != rep2:
                    view.wrong_message("Passwords do not match. Please try again.")
                    return
        return pwd

    def login(self, username: str, password: str):
        result = login(username, password)
        if result:
            token, refresh, expiry, refresh_hash = result
            update_access_token(token)
            return token
        return None

    def refresh(self):
        result = refresh_tokens()
        if result:
            token, refresh, expiry = result
            update_access_token(token)
            return token
        return None

    def logout(self):
        logout()

    def db_create(self):
        db_create()

    @require_elevated_privileges
    def manager_create(self):
        manager_create()
