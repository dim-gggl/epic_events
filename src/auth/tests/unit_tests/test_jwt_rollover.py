import datetime
import importlib

import jwt

import src.auth.jwt.config as cfg
from src.auth.jwt.verify_token import verify_access_token


def test_verify_allows_previous_secret(monkeypatch):
    # Configure a new current secret and an older previous secret
    monkeypatch.setenv("SECRET_KEY", "new-secret")
    monkeypatch.setenv("SECRET_KEY_PREV", "old-secret")
    monkeypatch.setenv("JWT_KID", "v2")
    monkeypatch.setenv("JWT_KID_PREV", "v1")
    
    importlib.reload(cfg)

    # Build a token signed with the previous secret and kid
    now = datetime.datetime.now(datetime.UTC)
    payload = {"sub": "42", "role_id": "3", "exp": now + datetime.timedelta(minutes=5)}
    token_prev = jwt.encode(payload, "old-secret", algorithm="HS256", headers={"kid": "v1"})

    decoded = verify_access_token(token_prev)
    assert decoded["sub"] == "42"
    assert decoded["role_id"] == "3"

