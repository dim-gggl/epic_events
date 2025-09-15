
import src.auth.permissions as perms


class DummyPerm:
    def __init__(self, name: str):
        self.name = name


class DummyRole:
    def __init__(self, rel=None, arr=None):
        self.permissions_rel = rel or []
        self.permissions = arr or []


class DummySession:
    def __init__(self, role):
        self._role = role
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def query(self, model):
        class _Q:
            def __init__(self, role):
                self._role = role
            def filter(self, *_, **__):
                return self
            def first(self):
                return self._role
        return _Q(self._role)


def test_has_permission_uses_db_normalized(monkeypatch):
    # Role 99 has normalized permissions via relation
    role = DummyRole(rel=[DummyPerm("client:update:own"), DummyPerm("client:view")])
    monkeypatch.setattr(perms, "Session", lambda: DummySession(role))
    monkeypatch.setattr(perms, "verify_access_token", lambda t: {"sub": "1", "role_id": "99"})

    assert perms.has_permission("tok", "client:update:own") is True
    assert perms.has_permission("tok", "user:create") is False


def test_has_permission_fallback_defaults(monkeypatch):
    # Force DB read to fail/return None to trigger fallback
    monkeypatch.setattr(perms, "_permissions_from_db", lambda role_id: None)
    # Commercial role (2) defaults include client:create, not user:create
    monkeypatch.setattr(perms, "verify_access_token", lambda t: {"sub": "5", "role_id": "2"})

    assert perms.has_permission("tok", "client:create") is True
    assert perms.has_permission("tok", "user:create") is False

