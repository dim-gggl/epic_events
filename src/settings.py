import os

from src.auth.utils import get_secret_key

# Epic Events CRM - Database Configuration

# PostgreSQL Database Configuration
POSTGRES_USER=os.environ.get("POSTGRES_USER", "epic_events_app")
POSTGRES_PASSWORD=os.environ.get(
    "POSTGRES_PASSWORD", "your_secure_password_here"
)
POSTGRES_HOST=os.environ.get("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT=os.environ.get("POSTGRES_PORT", 5432)
POSTGRES_DB=os.environ.get("POSTGRES_DB", "epic_events_db")

DATABASE_URL=os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# The secret key for the JWT
SECRET_KEY=os.environ.get("SECRET_KEY", "your_secret_key")

# Sentry will provide your personal dsn as soon as you get
# an account id.
SENTRY_DSN=os.environ.get("SENTRY_DSN", "your_DSN")

# By default set on 'development'
SENTRY_ENVIRONMENT=os.environ.get("SENTRY_ENVIRONMENT", "development")

# 0.0 to get no log and 1.0 for 100% of the log messages
SENTRY_TRACES_SAMPLE_RATE=os.environ.get("SENTRY_TRACES_SAMPLE_RATE", 9.0)

# The directory where is stored the authentication JWT
# in session. If set to None, the CRM will use the default
# temp dir to store the token. It is compatible with most
# of the OSs available, which is quiet practicle. But not so
# safe. You might prefer to set this variable yourself and
# not in a file.
TEMP_FILE_PATH=os.environ.get("TEMP_FILE_PATH", None)

# Token lifetimes
ACCESS_TOKEN_LIFETIME_MINUTES = os.environ.get(
    "ACCESS_TOKEN_LIFETIME_MINUTES", 30
)
REFRESH_TOKEN_LIFETIME_DAYS = os.environ.get(
    "REFRESH_TOKEN_LIFETIME_DAYS", 1
)

# By default username is accepted to be between 5 and 64 characters long
USERNAME_MIN_LENGTH = os.environ.get("USERNAME_MIN_LENGTH", 5)
USERNAME_MAX_LENGTH = os.environ.get("USERNAME_MAX_LENGTH", 64)

# Password is accepted to be between 8 and 128 characters long
PASSWORD_MIN_LENGTH = os.environ.get("PASSWORD_MIN_LENGTH", 8)
PASSWORD_MAX_LENGTH = os.environ.get("PASSWORD_MAX_LENGTH", 128)

# Initially the role ids were set 1, 2 and 3. Since the database
# had to be modified and some migrations were necessary since then,
# the role ids are now set to 1 to 9.
ROLE_MIN_ID = os.environ.get("ROLE_MIN_ID", 1)
ROLE_MAX_ID = os.environ.get("ROLE_MAX_ID", 9)


# --- JWT key rollover support ---
# We support a current key (identified by JWT_KID, default
# 'v1') and an optional previous key (SECRET_KEY_PREV) to
# allow seamless rotation.

# Current key id (appears in JWT header as 'kid')
CURRENT_KID = os.environ.get("JWT_KID", "v1")

# Current secret (mandatory). Do not implicitly load from .env
# here; tests expect a failure when SECRET_KEY is absent in
# the environment.
CURRENT_SECRET = os.environ.get("SECRET_KEY")
if not CURRENT_SECRET:
    CURRENT_SECRET = get_secret_key()

# Optional previous secret for rollover windows
PREVIOUS_SECRET = os.environ.get("SECRET_KEY_PREV")
PREVIOUS_KID = os.environ.get("JWT_KID_PREV", "v0")

# Registry of acceptable keys by kid
SECRET_KEYS: dict[str, str] = {CURRENT_KID: CURRENT_SECRET}
