import os

from src.auth.utils import get_secret_key
from src.data_access.config import _build_url as get_database_url



# Token lifetimes
ACCESS_TOKEN_LIFETIME_MINUTES = 30
REFRESH_TOKEN_LIFETIME_DAYS = 1

SECRET_KEY = get_secret_key()

# --- JWT key rollover support ---
# We support a current key (identified by JWT_KID, default 'v1') and an optional
# previous key (SECRET_KEY_PREV) to allow seamless rotation.

# Current key id (appears in JWT header as 'kid')
CURRENT_KID = os.environ.get("JWT_KID", "v1")

# Current secret (mandatory). Do not implicitly load from .env here; tests
# expect a failure when SECRET_KEY is absent in the environment.
CURRENT_SECRET = SECRET_KEY  # reads SECRET_KEY

# Optional previous secret for rollover windows
PREVIOUS_SECRET = os.environ.get("SECRET_KEY_PREV")
PREVIOUS_KID = os.environ.get("JWT_KID_PREV", "v0")

# Registry of acceptable keys by kid
SECRET_KEYS: dict[str, str] = {CURRENT_KID: CURRENT_SECRET}
if PREVIOUS_SECRET:
    SECRET_KEYS[PREVIOUS_KID] = PREVIOUS_SECRET

DATABASE_URL = os.environ.get("DATABASE_URL", get_database_url())

def get_current_kid() -> str:
    return CURRENT_KID

def get_secret_by_kid(kid: str | None) -> str:
    """Return secret for given kid; fall back to current if None/unknown."""
    if kid and kid in SECRET_KEYS:
        return SECRET_KEYS[kid]
    # Unknown or absent kid: try current first (legacy tokens without kid)
    return CURRENT_SECRET

def get_all_secrets() -> list[str]:
    """Return all accepted secrets (current first, then previous)."""
    secrets = [CURRENT_SECRET]
    if PREVIOUS_SECRET:
        secrets.append(PREVIOUS_SECRET)
    return secrets
