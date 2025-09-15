import datetime

import bcrypt

import src.auth.jwt.refresh_token as refresh_mod


class DummyUser:
    def __init__(self, id: int, role_id: int, refresh_hash: str | None):
        self.id = id
        self.role_id = role_id
        self.refresh_token_hash = refresh_hash


class DummySession:
    def __init__(self, user: DummyUser | None):
        self._user = user
        self._committed = False
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def get(self, model, id):
        return self._user
    def commit(self):
        self._committed = True


def _bcrypt_hash(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def test_refresh_success_rotation(monkeypatch, dummy_view):
    # Stored session with a valid refresh token r1
    stored = {
        "access_token": "acc1",
        "refresh_token": "r1",
        "refresh_expiry": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        "user_id": 5,
        "role_id": 2,
        "stored_at": datetime.datetime.now(datetime.UTC),
    }

    # DB user whose refresh hash matches r1
    user = DummyUser(5, 2, _bcrypt_hash("r1"))

    # Make generate_token return a deterministic new pair r2
    new_exp = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    def fake_generate(uid, rid):
        return ("acc2", "r2", new_exp, bcrypt.hashpw(b"r2", bcrypt.gensalt()))

    captured = {"stored": None}
    def fake_store(access, refresh, exp, uid, role_id):
        captured["stored"] = (access, refresh, exp, uid, role_id)

    monkeypatch.setattr(refresh_mod, "get_stored_token", lambda: stored)
    monkeypatch.setattr(refresh_mod,
                        "get_user_info_from_token",
                        lambda: {"user_id": 5, "role_id": 2})
    monkeypatch.setattr(refresh_mod, "Session", lambda: DummySession(user))
    monkeypatch.setattr(refresh_mod, "generate_token", fake_generate)
    monkeypatch.setattr(refresh_mod, "store_token", fake_store)
    monkeypatch.setattr(refresh_mod, "view", dummy_view)

    res = refresh_mod.refresh_tokens()
    assert res is not None
    new_access, new_refresh, new_expiry = res
    assert new_access == "acc2"
    assert new_refresh == "r2"
    assert captured["stored"][1] == "r2"  # persisted
    # DB hash updated to match r2
    assert bcrypt.checkpw(b"r2", user.refresh_token_hash.encode("utf-8"))
    # Success message displayed
    assert any(kind == "success" for kind, _ in dummy_view.get_messages())


def test_refresh_invalid_hash(monkeypatch, dummy_view):
    stored = {
        "access_token": "acc1",
        "refresh_token": "r1",
        "refresh_expiry": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        "user_id": 5,
        "role_id": 2,
        "stored_at": datetime.datetime.now(datetime.UTC),
    }
    # DB user has a different refresh hash
    user = DummyUser(5, 2, _bcrypt_hash("DIFFERENT"))

    monkeypatch.setattr(refresh_mod, "get_stored_token", lambda: stored)
    monkeypatch.setattr(refresh_mod,
                        "get_user_info_from_token",
                        lambda: {"user_id": 5, "role_id": 2})
    monkeypatch.setattr(refresh_mod, "Session", lambda: DummySession(user))
    monkeypatch.setattr(refresh_mod, "view", dummy_view)

    res = refresh_mod.refresh_tokens()
    assert res is None
    assert any(
        "Invalid refresh token" in msg for kind,
        msg in dummy_view.get_messages() if kind == "wrong"
    )


def test_refresh_expired_token(monkeypatch, dummy_view):
    stored = {
        "access_token": "acc1",
        "refresh_token": "r1",
        "refresh_expiry": datetime.datetime.now(datetime.UTC) - \
        datetime.timedelta(seconds=1),
        "user_id": 5,
        "role_id": 2,
        "stored_at": datetime.datetime.now(datetime.UTC),
    }

    monkeypatch.setattr(refresh_mod, "get_stored_token", lambda: stored)
    monkeypatch.setattr(refresh_mod, "view", dummy_view)
    monkeypatch.setattr(refresh_mod,
                        "get_user_info_from_token",
                        lambda: {"user_id": 5, "role_id": 2})

    res = refresh_mod.refresh_tokens()
    assert res is None
    assert any(
        "expired" in msg.lower() for kind, msg in dummy_view.get_messages() if kind == "wrong"
    )

