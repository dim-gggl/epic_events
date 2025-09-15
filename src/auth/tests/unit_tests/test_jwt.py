import datetime
import importlib
import os

import jwt
import pytest

from src.auth.jwt.generate_token import generate_token
from src.auth.jwt.verify_token import verify_access_token
from src.auth.utils import get_secret_key
from src.exceptions import ExpiredTokenError, InvalidTokenError


def test_generate_token_success(monkeypatch):
    access, raw_refresh, refresh_exp, refresh_hash = generate_token(10, 2)

    assert isinstance(access, str)
    assert isinstance(raw_refresh, str)
    assert isinstance(refresh_exp, datetime.datetime)
    assert isinstance(refresh_hash, (bytes, bytearray))

    # Access token should be decodable with our secret and contain claims
    payload = jwt.decode(access, key=get_secret_key(), algorithms=["HS256"])
    assert payload["sub"] == "10"
    assert payload["role_id"] == "2"
    assert "exp" in payload


def test_generate_token_missing_secret(monkeypatch):
    # Remove SECRET_KEY and ensure config reload fails (no current secret)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    import src.auth.jwt.config as cfg
    with pytest.raises(RuntimeError):
        importlib.reload(cfg)


def test_verify_access_token_valid():
    # Create a valid token
    now = datetime.datetime.now(datetime.UTC)
    payload = {"sub": "7", "role_id": "3", "exp": now + datetime.timedelta(minutes=5)}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")

    decoded = verify_access_token(token)
    assert decoded["sub"] == "7"
    assert decoded["role_id"] == "3"


def test_generate_token_header_contains_kid(monkeypatch):
    # Ensure a specific KID is used
    monkeypatch.setenv("JWT_KID", "v9")
    # Reload config to pick up env
    import src.auth.jwt.config as cfg
    importlib.reload(cfg)
    # Generate token and inspect header
    access, _, _, _ = generate_token(123, 1)
    header = jwt.get_unverified_header(access)
    assert header.get("kid") == os.environ.get("JWT_KID", "v1")


def test_verify_access_token_no_token():
    with pytest.raises(InvalidTokenError):
        verify_access_token("")


def test_verify_access_token_missing_fields():
    now = datetime.datetime.now(datetime.UTC)
    payload = {"sub": "7", "exp": now + datetime.timedelta(minutes=5)}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        verify_access_token(token)


def test_verify_access_token_expired():
    past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=1)
    payload = {"sub": "7", "role_id": "3", "exp": past}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")

    with pytest.raises(ExpiredTokenError):
        verify_access_token(token)

