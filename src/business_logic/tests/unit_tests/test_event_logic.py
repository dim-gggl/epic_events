import pytest

import src.business_logic.event_logic as el


class DummyEvent:
    def __init__(self, id=1):
        self.id = id


class DummyContract:
    def __init__(self, is_signed: bool):
        self.is_signed = is_signed


def test_create_event_requires_signed_contract(monkeypatch, make_session):
    # Not found
    class CRepo1:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "contract_repository", CRepo1())
    with pytest.raises(ValueError):
        el.event_logic.create_event("tok", {"contract_id": 1})

    # Unsigned -> raises
    class CRepo2:
        def get_by_id(self, id, session):
            return DummyContract(is_signed=False)
    monkeypatch.setattr(el, "contract_repository", CRepo2())
    with pytest.raises(ValueError):
        el.event_logic.create_event("tok", {"contract_id": 1})

    # Signed -> ok
    created = {"ok": False}
    class CRepo3:
        def get_by_id(self, id, session):
            return DummyContract(is_signed=True)
    class ERepo:
        def create(self, data, session):
            created["ok"] = True
            return DummyEvent(2)
    monkeypatch.setattr(el, "contract_repository", CRepo3())
    monkeypatch.setattr(el, "event_repository", ERepo())

    e = el.event_logic.create_event("tok", {"contract_id": 2})
    assert isinstance(e, DummyEvent)
    assert created["ok"] is True


def test_get_events_filtered_and_all(monkeypatch, make_session):
    class Repo:
        def find_by(self, session, **kwargs):
            return [DummyEvent(1)]
        def get_all(self, session):
            return [DummyEvent(1), DummyEvent(2)]
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo())

    filtered = el.event_logic.get_events("tok", user_id=3, filtered=True)
    all_ = el.event_logic.get_events("tok", user_id=3, filtered=False)
    assert len(filtered) == 1
    assert len(all_) == 2


def test_get_event_by_id(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return DummyEvent(id)
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo())
    e = el.event_logic.get_event_by_id("tok", 9)
    assert e.id == 9


def test_update_event_absent_returns_none(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo())
    assert el.event_logic.update_event("tok", 1, 2, {"title": "X"}) is None


def test_update_event_success(monkeypatch, make_session):
    e = DummyEvent(3)
    class Repo:
        def get_by_id(self, id, session):
            return e
        def update(self, id, data, session):
            return e
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo())
    assert el.event_logic.update_event("tok", 1, 3, {"title": "Y"}) is e


def test_assign_support_to_event(monkeypatch, make_session):
    e = DummyEvent(4)
    class Repo:
        def get_by_id(self, id, session):
            return e
        def update(self, id, data, session):
            return e
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo())
    assert el.event_logic.assign_support_to_event("tok", 4, 10) is e


def test_delete_event_rules(monkeypatch, make_session):
    # Not found
    class Repo1:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(el, "Session", lambda: make_session())
    monkeypatch.setattr(el, "event_repository", Repo1())
    assert el.event_logic.delete_event("tok", 1) is None

    # Success delete
    class Repo2:
        def get_by_id(self, id, session):
            return DummyEvent(2)
        def delete(self, id, session):
            return True
    monkeypatch.setattr(el, "event_repository", Repo2())
    assert el.event_logic.delete_event("tok", 2) is True


