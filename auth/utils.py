import os

def get_secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if not value:
        raise RuntimeError("SECRET_KEY is not set")
    return value