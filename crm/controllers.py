from auth.validators import verify_access_token
from exceptions import InvalidTokenError, OperationDeniedError
from crm.views import view


def clean_details(raw_details: list[dict]) -> list[dict]:
    """Clean the details of all users"""
    details = {}
    for user in raw_details:
        details["username"] = validate_username(raw_details["username"].strip())
        details["full_name"] = validate_full_name(raw_details["full_name"].strip())
        details["email"] = validate_email(raw_details["email"].strip())
        details["role"] = validate_role(raw_details["role"].strip())
        details["password_hash"] = raw_details["password_hash"]
    return details

def get_users_infos(access_token: str) -> list[dict]:
    """Get the details of all users"""
    payload = verify_access_token(access_token)
    if payload is None:
        raise InvalidTokenError()
    if payload["role_id"] != "2":
        raise OperationDeniedError()
    else:
        raw_details = view.get_users_details()
        details = clean_details(raw_details)
    return details

def login_menu():
    view.display_login_menu()

