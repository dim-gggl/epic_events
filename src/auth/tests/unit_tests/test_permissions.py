import pytest

import src.auth.permissions as perms
from src.exceptions import InvalidTokenError


def test_get_user_id_and_role_from_token(monkeypatch):
    monkeypatch.setattr(perms, "verify_access_token", lambda t: {"sub": "42", "role_id": "3"})
    user_id, role_id = perms.get_user_id_and_role_from_token("any")
    assert user_id == 42
    assert role_id == 3


def test_get_user_id_and_role_missing_token():
    with pytest.raises(PermissionError):
        perms.get_user_id_and_role_from_token("")


def test_has_permission_true_and_false(monkeypatch):
    # Management role (1) should have user:create
    monkeypatch.setattr(perms, 
                        "verify_access_token", 
                        lambda t: {"sub": "1", "role_id": "1"})
    assert perms.has_permission("tok", "user:create") is True

    # Support role (3) should not have client:create
    monkeypatch.setattr(perms, 
                        "verify_access_token", 
                        lambda t: {"sub": "2", "role_id": "3"})
    assert perms.has_permission("tok", "client:create") is False


def test_login_required_decorator_with_kwarg(monkeypatch):
    monkeypatch.setattr(perms, 
                        "verify_access_token", 
                        lambda t: {"sub": "5", "role_id": "2"})

    @perms.login_required
    def protected(*, access_token: str):
        return "ok"

    assert protected(access_token="abc") == "ok"


def test_login_required_decorator_invalid_token(monkeypatch):
    def _raise(_):
        raise InvalidTokenError("bad")
    monkeypatch.setattr(perms, "verify_access_token", _raise)

    @perms.login_required
    def protected(*, access_token: str):
        return "ok"

    with pytest.raises(PermissionError):
        protected(access_token="abc")


def test_require_permission_decorator(monkeypatch):
    # Allow path
    monkeypatch.setattr(perms, "has_permission", lambda tok, perm: True)

    @perms.require_permission("user:create")
    def create_user(*, access_token: str):
        return 123

    assert create_user(access_token="tok") == 123

    # Deny path
    monkeypatch.setattr(perms, "has_permission", lambda tok, perm: False)

    @perms.require_permission("client:create")
    def create_client(*, access_token: str):
        return 1

    with pytest.raises(PermissionError):
        create_client(access_token="tok")
