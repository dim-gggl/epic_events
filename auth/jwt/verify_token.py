import jwt
from .config import SECRET_KEY
from ...exceptions import InvalidTokenError, ExpiredTokenError

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()
    return payload
