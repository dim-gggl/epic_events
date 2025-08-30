import os
import psycopg

from db.config import engine, Session


DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = get_secret_key()
ACCESS_TOKEN_LIFETIME_MINUTES = 30
REFRESH_TOKEN_LIFETIME_DAYS = 7


conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()
