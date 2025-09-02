from auth.validators import is_valid_username, is_valid_email, is_valid_password, is_valid_role_id
from auth.jwt.verify_token import verify_access_token
from exceptions import InvalidTokenError, OperationDeniedError
from crm.views.views import MainView as view
view = view()

class MainController:

    def get_username(self) -> str:
        username = view.get_username().strip()
        if not is_valid_username(username):
            view.wrong_message("Username should be between 5 and 64 characters long.\n"
                              "and should not already be in use.")
            return self.get_username()
        return username
    
    def get_full_name(self) -> str:
        full_name = view.get_full_name().strip()
        return full_name

    def get_email(self) -> str:
        email = view.get_email().strip()
        if not is_valid_email(email):
            view.wrong_message("Invalid email address.")
            return self.get_email()
        return email
        
    def get_password(self) -> str:
        password = view._prompt_password().strip()
        if not is_valid_password(password):
            view.wrong_message("Password should be at least 8 characters long\n"
                              "and contain at least one uppercase letter, one\n"
                              "lowercase letter and one digit.")
            return self.get_password()
        return password

    def get_role_id(self) -> int:
        role_id = int(view.get_role_id().strip())
        if not is_valid_role_id(role_id):
            view.wrong_message("Invalid role id.")
            return self.get_role_id()
        return role_id

    def get_access_token_payload(self) -> dict:
        access_token = view.get_access_token().strip()
        payload = verify_access_token(access_token)
        if payload is None:
            view.wrong_message("Invalid access token.")
            return self.get_access_token_payload()
        return payload
        

