import jwt
from auth.utils import get_secret_key
from crm.views.views import MainView as view
from exceptions import InvalidTokenError, ExpiredTokenError

view = view()

SECRET_KEY = get_secret_key()


def verify_access_token(token: str):
    payload = None
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        view.wrong_message("EXPIRED SIGNATURE IN YOUR TOKEN")
    except jwt.InvalidTokenError:
        view.wrong_message("INVALID TOKEN")
    return payload
