import jwt
from auth.utils import get_secret_key
from crm.views.views import MainView
from exceptions import InvalidTokenError, ExpiredTokenError

view = MainView()

SECRET_KEY = get_secret_key()


def verify_access_token(token: str) -> dict | str:
    """
    Verify JWT access token and return payload.
    
    Args:
        token: JWT access token string
        
    Returns:
        dict: Token payload containing user information
        str: If the payload cannot be extracted from the JWT,
        returns an error message containing the necessary
        information to understand what failed.
        
    """
    if not token:
        view.wrong_message("You must authenticate first.")
        
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
        # Validate that required fields are present
        if 'sub' not in payload or 'role_id' not in payload:
            raise InvalidTokenError("Token missing required fields")
        return payload

    except jwt.ExpiredSignatureError as e:
        reason = f"EXPIRED SIGNATURE IN YOUR TOKEN\n{e}"
        view.wrong_message(reason)
        return reason

    except jwt.InvalidTokenError as e:
        reason = f"INVALID TOKEN\n{str(e)}"
        view.wrong_message(reason)
        return reason

    except Exception as e:
        reason = f"TOKEN VERIFICATION FAILED \n{str(e)}"
        view.wrong_message(reason)
        return reason

