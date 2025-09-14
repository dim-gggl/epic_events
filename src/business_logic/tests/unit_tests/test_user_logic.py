import pytest

import src.business_logic.user_logic as ul


class DummyUser:
    def __init__(self, id=1):
        self.id = id
        self.managed_clients = []
        self.managed_contracts = []
        self.supported_events = []


def test_create_user(monkeypatch, make_session):
    created = {}
    class Repo:
        def create(self, data, session):
            created.update(data)
            return DummyUser(2)

    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", Repo())
    monkeypatch.setattr(ul, "hash_password", lambda p: "hashed")

    data = {"username": "john", "full_name": "John", "email": "j@x", "password": "Abcdefg1", "role_id": 2}
    user = ul.user_logic.create_user("tok", data)

    assert isinstance(user, DummyUser)
    assert created["password_hash"] == "hashed"
    assert "password" not in created


def test_get_users(monkeypatch, make_session):
    class Repo:
        def get_all(self, session):
            return [DummyUser(1), DummyUser(2)]
    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", Repo())

    users = ul.user_logic.get_users("tok")
    assert len(users) == 2


def test_get_user_by_id_loads_relationships(monkeypatch, make_session):
    u = DummyUser(3)
    class Repo:
        def get_by_id(self, id, session):
            return u
    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", Repo())

    user = ul.user_logic.get_user_by_id("tok", 3)
    assert user is u


def test_update_user_checks_permission(monkeypatch, make_session):
    u = DummyUser(4)
    updated = {"v": None}
    class Repo:
        def get_by_id(self, id, session):
            return u
        def update(self, id, data, session):
            updated["v"] = data
            return u

    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", Repo())
    # allow has_permission_for_user
    monkeypatch.setattr(ul, "has_permission_for_user", lambda tok, action, target, user_id: True)

    result = ul.user_logic.update_user("tok", 4, {"full_name": "New"})
    assert result is u
    assert updated["v"] == {"full_name": "New"}


def test_update_user_forbidden(monkeypatch, make_session):
    u = DummyUser(5)
    class Repo:
        def get_by_id(self, id, session):
            return u

    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", Repo())
    monkeypatch.setattr(ul, "has_permission_for_user", lambda *a, **k: False)

    with pytest.raises(PermissionError):
        ul.user_logic.update_user("tok", 5, {"x": 1})


def test_delete_user_rules(monkeypatch, make_session):
    # Cannot delete self
    monkeypatch.setattr(ul, "Session", lambda: make_session())
    monkeypatch.setattr(ul, "user_repository", object())
    with pytest.raises(ValueError):
        ul.user_logic.delete_user("tok", 1, 1)

    # Target not found returns False
    class Repo2:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(ul, "user_repository", Repo2())
    assert ul.user_logic.delete_user("tok", 1, 2) is False

    # With associations -> raises
    user_with_rel = DummyUser(3)
    user_with_rel.managed_clients = [1]
    class Repo3:
        def get_by_id(self, id, session):
            return user_with_rel
    monkeypatch.setattr(ul, "user_repository", Repo3())
    with pytest.raises(ValueError):
        ul.user_logic.delete_user("tok", 1, 3)

    # Successful delete
    class Repo4:
        def __init__(self):
            self._u = DummyUser(4)
        def get_by_id(self, id, session):
            return self._u
        def delete(self, id, session):
            return True
    monkeypatch.setattr(ul, "user_repository", Repo4())
    assert ul.user_logic.delete_user("tok", 1, 4) is True


