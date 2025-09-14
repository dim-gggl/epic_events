import pytest

import src.business_logic.contract_logic as col


class DummyContract:
    def __init__(self, id=1):
        self.id = id
        self.events = []
        self.client = object()


def test_create_contract(monkeypatch, make_session):
    class Repo:
        def create(self, data, session):
            c = DummyContract(2)
            return c
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo())

    c = col.contract_logic.create_contract("tok", {"client_id": 1, "commercial_id": 2, "total_amount": 100, "remaining_amount": 100})
    assert isinstance(c, DummyContract)


def test_get_contracts_filtered_and_all(monkeypatch, make_session):
    class Repo:
        def find_by(self, session, **kwargs):
            return [DummyContract(1)]
        def get_all(self, session):
            return [DummyContract(1), DummyContract(2)]
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo())

    filtered = col.contract_logic.get_contracts("tok", user_id=5, filtered=True)
    all_ = col.contract_logic.get_contracts("tok", user_id=5, filtered=False)
    assert len(filtered) == 1
    assert len(all_) == 2


def test_get_contract_by_id_loads_events(monkeypatch, make_session):
    c = DummyContract(3)
    class Repo:
        def get_by_id(self, id, session):
            return c
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo())

    out = col.contract_logic.get_contract_by_id("tok", 3)
    assert out is c


def test_update_contract_absent_returns_none(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo())
    assert col.contract_logic.update_contract("tok", 1, 2, {"x": 1}) is None


def test_update_contract_success(monkeypatch, make_session):
    c = DummyContract(4)
    class Repo:
        def get_by_id(self, id, session):
            return c
        def update(self, id, data, session):
            return c
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo())
    assert col.contract_logic.update_contract("tok", 1, 4, {"remaining_amount": 50}) is c


def test_delete_contract_rules(monkeypatch, make_session):
    # Not found
    class Repo1:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "contract_repository", Repo1())
    assert col.contract_logic.delete_contract("tok", 1) is None

    # With events -> raises
    has_events = DummyContract(2)
    class Repo2:
        def get_by_id(self, id, session):
            return has_events
    class EventRepo:
        def find_by(self, session, **kwargs):
            return [object()]
    monkeypatch.setattr(col, "contract_repository", Repo2())
    monkeypatch.setattr(col, "event_repository", EventRepo())
    with pytest.raises(ValueError):
        col.contract_logic.delete_contract("tok", 2)

    # Success delete
    class Repo3:
        def get_by_id(self, id, session):
            return DummyContract(3)
        def delete(self, id, session):
            return True
    monkeypatch.setattr(col, "contract_repository", Repo3())
    class EventRepo2:
        def find_by(self, session, **kwargs):
            return []
    monkeypatch.setattr(col, "event_repository", EventRepo2())
    assert col.contract_logic.delete_contract("tok", 3) is True


