from datetime import UTC, datetime

import src.auth.login as login_mod


class DummyUser:
    def __init__(self, id: int, username: str, role_id: int, password_hash: str):
        self.id = id
        self.username = username
        self.role_id = role_id
        self.password_hash = password_hash
        self.refresh_token_hash = None


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


def test_login_success(monkeypatch, dummy_view):
    # Arrange: user exists and password verifies, token generation returns known values
    user = DummyUser(1, "john", 2, "hash")

    monkeypatch.setattr(login_mod, "Session", lambda: DummySession(user))
    monkeypatch.setattr(login_mod, "verify_password", lambda p, h: True)
    monkeypatch.setattr(login_mod, "generate_token", lambda uid, rid: ("acc", "raw", datetime.now(UTC), b"h"))

    # Capture token storage and view outputs
    calls = {}
    def _store(access, refresh, exp, uid, rid):
        calls["store"] = (access, refresh, exp, uid, rid)
    monkeypatch.setattr(login_mod, "store_token", _store)
    monkeypatch.setattr(login_mod, "view", dummy_view)

    # Avoid interactive password prompt
    monkeypatch.setattr(login_mod.getpass, "getpass", lambda: "pwd")

    result = login_mod.login("john")

    assert result[0] == "acc"
    assert result[1] == "raw"
    assert isinstance(result[2], datetime)
    assert isinstance(result[3], (bytes, bytearray))
    assert calls["store"][0] == "acc"
    assert any(kind == "success" for kind, _ in dummy_view.get_messages())


def test_login_unknown_username(monkeypatch, dummy_view):
    monkeypatch.setattr(login_mod, "Session", lambda: DummySession(None))
    monkeypatch.setattr(login_mod, "view", dummy_view)
    monkeypatch.setattr(login_mod.getpass, "getpass", lambda: "pwd")

    assert login_mod.login("unknown") is None
    assert any(
        "Unknown username" in msg for kind, 
        msg in dummy_view.get_messages() if kind == "wrong"
    )


def test_login_wrong_password(monkeypatch, dummy_view):
    user = DummyUser(1, "john", 2, "hash")
    monkeypatch.setattr(login_mod, "Session", lambda: DummySession(user))
    monkeypatch.setattr(login_mod, "verify_password", lambda p, h: False)
    monkeypatch.setattr(login_mod, "view", dummy_view)
    monkeypatch.setattr(login_mod.getpass, "getpass", lambda: "pwd")

    assert login_mod.login("john") is None
    assert any("Wrong password" in msg for kind, msg in dummy_view.get_messages() if kind == "wrong")


