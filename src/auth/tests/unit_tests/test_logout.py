from datetime import datetime, timezone

import pytest

import src.auth.logout as logout_mod


class DummyUser:
    def __init__(self, id: int):
        self.id = id
        self.last_login = None


class DummyQuery:
    def __init__(self, user: DummyUser | None):
        self._user = user
    def filter(self, *args, **kwargs):
        return self
    def __bool__(self):
        return self._user is not None
    def __getattr__(self, item):
        raise AttributeError(item)


class DummySession:
    def __init__(self, user: DummyUser | None):
        self._user = user
        self._committed = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def query(self, model):
        return DummyQuery(self._user)
    def commit(self):
        self._committed = True


def test_logout_success(monkeypatch, dummy_view):
    user = DummyUser(1)
    monkeypatch.setattr(logout_mod, "get_user_info_from_token", lambda: {"user_id": 1, "role_id": 2})
    monkeypatch.setattr(logout_mod, "Session", lambda: DummySession(user))
    did_cleanup = {"v": False}
    def _cleanup():
        did_cleanup["v"] = True
    monkeypatch.setattr(logout_mod, "cleanup_token_file", _cleanup)
    monkeypatch.setattr(logout_mod, "view", dummy_view)

    logout_mod.logout()

    assert did_cleanup["v"] is True
    assert any(kind == "success" for kind, _ in dummy_view.get_messages())


def test_logout_no_active_session(monkeypatch, dummy_view):
    monkeypatch.setattr(logout_mod, "get_user_info_from_token", lambda: None)
    monkeypatch.setattr(logout_mod, "view", dummy_view)

    logout_mod.logout()

    assert any("No active session" in msg for kind, msg in dummy_view.get_messages() if kind == "wrong")


