from datetime import UTC, datetime

import src.auth.login as login_mod


class DummyUser:
    def __init__(self, id: int, username: str, role_id: int, password_hash: str):
        self.id = id
        self.username = username
        self.role_id = role_id
        self.password_hash = password_hash
        self.refresh_token_hash = None
        self.last_login = None


class DummySession:
    def __init__(self, user: DummyUser | None):
        self._user = user
        self._committed = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def scalars(self, stmt):
        class _Scalars:
            def __init__(self, user):
                self.user = user
            def first(self):
                return self.user
        return _Scalars(self._user)
    def commit(self):
        self._committed = True


def test_login_sets_last_login(monkeypatch, dummy_view):
    user = DummyUser(1, "john", 2, "hash")

    monkeypatch.setattr(login_mod, "Session", lambda: DummySession(user))
    monkeypatch.setattr(login_mod, "verify_password", lambda p, h: True)
    # deterministic token generation
    monkeypatch.setattr(login_mod, "generate_token", lambda uid, rid: ("acc", "raw", datetime.now(UTC), b"h"))
    captured = {}
    monkeypatch.setattr(login_mod, "store_token", lambda *args: captured.setdefault("s", args))
    monkeypatch.setattr(login_mod, "view", dummy_view)

    login_mod.login("john", "pass")

    assert isinstance(user.last_login, datetime)
    assert user.last_login.tzinfo is not None

