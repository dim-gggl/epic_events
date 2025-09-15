import os
from datetime import UTC, datetime, timedelta

from src.auth.jwt import token_storage as ts


def test_store_and_read_token(isolated_token_file, dummy_view):
    now = datetime.now(UTC)
    ts.store_token("acc", "raw", now + timedelta(days=1), 5, 2)

    data = ts.get_stored_token()
    assert data is not None
    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "raw"
    assert isinstance(data["refresh_expiry"], datetime)
    assert isinstance(data["stored_at"], datetime)
    assert data["user_id"] == 5
    assert data["role_id"] == 2


def test_get_access_and_user_info(isolated_token_file):
    now = datetime.now(UTC)
    ts.store_token("token123", "r", now + timedelta(days=1), 1, 3)

    assert ts.get_access_token() == "token123"
    assert ts.get_user_info_from_token() == {"user_id": 1, "role_id": 3}


def test_update_access_token(isolated_token_file):
    now = datetime.now(UTC)
    ts.store_token("old", "r", now + timedelta(days=1), 1, 1)
    ts.update_access_token("new")
    assert ts.get_access_token() == "new"


def test_cleanup_token_file(isolated_token_file, dummy_view):
    now = datetime.now(UTC)
    ts.store_token("a", "b", now + timedelta(days=1), 1, 1)
    assert os.path.exists(isolated_token_file)
    ts.cleanup_token_file()
    assert not os.path.exists(isolated_token_file)


def test_invalid_json_triggers_cleanup_and_returns_none(isolated_token_file, dummy_view):
    # Write invalid JSON
    with open(isolated_token_file, "w") as f:
        f.write("{invalid json}")

    data = ts.get_stored_token()
    assert data is None
    # File should be removed by cleanup
    assert not os.path.exists(isolated_token_file)
    # Error message captured
    assert any(kind == "wrong" for kind, _ in dummy_view.get_messages())


def test_empty_file_triggers_cleanup_and_returns_none(isolated_token_file, dummy_view):
    # Create empty file
    with open(isolated_token_file, "w") as f:
        f.write("")

    data = ts.get_stored_token()
    assert data is None
    assert not os.path.exists(isolated_token_file)


def test_cleanup_when_no_file_shows_info(isolated_token_file, dummy_view):
    # Ensure file does not exist
    if os.path.exists(isolated_token_file):
        os.remove(isolated_token_file)
    ts.cleanup_token_file()
    assert ("display", "No token stored in the file") in dummy_view.get_messages()


