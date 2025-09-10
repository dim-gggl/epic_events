import os
from dotenv import load_dotenv

from src.auth.utils import get_secret_key
from src.data_access.config import _build_url

load_dotenv()


DATABASE_URL = os.environ.get("DATABASE_URL", _build_url())
SECRET_KEY = get_secret_key()
ACCESS_TOKEN_LIFETIME_MINUTES = 30
REFRESH_TOKEN_LIFETIME_DAYS = 1
