import pytest

import src.business_logic.client_logic as cl


class DummyClient:
    def __init__(self, id=1):
        self.id = id


def test_create_client(monkeypatch, make_session):
    created = {}
    class Repo:
        def create(self, data, session):
            created.update(data)
            return DummyClient(2)
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo())

    client = cl.client_logic.create_client("tok", {"full_name": "A", "email": "a@b"}, commercial_id=9)
    assert isinstance(client, DummyClient)
    assert created["commercial_id"] == 9


def test_get_clients_filtered_and_all(monkeypatch, make_session):
    class Repo:
        def find_by(self, session, **kwargs):
            return [DummyClient(1)]
        def get_all(self, session):
            return [DummyClient(1), DummyClient(2)]
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo())

    filtered = cl.client_logic.get_clients("tok", user_id=5, filtered=True)
    all_ = cl.client_logic.get_clients("tok", user_id=5, filtered=False)
    assert len(filtered) == 1
    assert len(all_) == 2


def test_get_client_by_id(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return DummyClient(id)
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo())

    c = cl.client_logic.get_client_by_id("tok", 7)
    assert c.id == 7


def test_update_client_when_absent_returns_none(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo())

    assert cl.client_logic.update_client("tok", 1, 2, {"x": 1}) is None


def test_update_client_success(monkeypatch, make_session):
    c = DummyClient(3)
    updated = {"v": None}
    class Repo:
        def get_by_id(self, id, session):
            return c
        def update(self, id, data, session):
            updated["v"] = data
            return c
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo())

    out = cl.client_logic.update_client("tok", 1, 3, {"email": "x@y"})
    assert out is c
    assert updated["v"] == {"email": "x@y"}


def test_delete_client_rules(monkeypatch, make_session):
    # Not found returns None
    class Repo1:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(cl, "Session", lambda: make_session())
    monkeypatch.setattr(cl, "client_repository", Repo1())
    assert cl.client_logic.delete_client("tok", 1) is None

    # With contracts -> raises
    class Repo2:
        def get_by_id(self, id, session):
            return DummyClient(id)
    class ContractRepo:
        def find_by(self, session, **kwargs):
            return [object()]
    monkeypatch.setattr(cl, "client_repository", Repo2())
    monkeypatch.setattr(cl, "contract_repository", ContractRepo())
    with pytest.raises(ValueError):
        cl.client_logic.delete_client("tok", 2)

    # Successful delete
    class Repo3:
        def get_by_id(self, id, session):
            return DummyClient(id)
        def delete(self, id, session):
            return True
    monkeypatch.setattr(cl, "client_repository", Repo3())
    # Ensure no contracts for this client in the success path
    class ContractRepo2:
        def find_by(self, session, **kwargs):
            return []
    monkeypatch.setattr(cl, "contract_repository", ContractRepo2())
    assert cl.client_logic.delete_client("tok", 3) is True


