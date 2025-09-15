import pytest

import src.business_logic.client_logic as cl
import src.business_logic.contract_logic as col
import src.business_logic.event_logic as el


class DummySession:
    def __init__(self):
        self._committed = False
        self._refreshed = []
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def commit(self):
        self._committed = True
    def refresh(self, obj):
        self._refreshed.append(obj)


class Client:
    def __init__(self, id, commercial_id):
        self.id = id
        self.commercial_id = commercial_id


class Contract:
    def __init__(self, id, client_id, commercial_id, is_signed=True):
        self.id = id
        self.client_id = client_id
        self.commercial_id = commercial_id
        self.is_signed = is_signed
        self.events = []


class Event:
    def __init__(self, id, contract_id, support_contact_id=None):
        self.id = id
        self.contract_id = contract_id
        self.support_contact_id = support_contact_id
        self.title = "E"


@pytest.fixture(autouse=True)
def stub_session(monkeypatch):
    monkeypatch.setattr(cl, "Session", lambda: DummySession())
    monkeypatch.setattr(col, "Session", lambda: DummySession())
    monkeypatch.setattr(el, "Session", lambda: DummySession())


def _stub_token(monkeypatch, user_id: int, role_id: int):
    # Stub token decoding in policy helpers
    import src.auth.policy as policy
    monkeypatch.setattr(policy, "get_user_id_and_role_from_token", lambda tok: (user_id, role_id))


def _stub_permissions(monkeypatch, perms: set[str]):
    import src.auth.policy as policy
    monkeypatch.setattr(policy, "get_effective_permissions", lambda role_id: set(perms))


def test_client_update_own_vs_any(monkeypatch):
    # Repository returning a client owned by commercial 7
    client = Client(1, commercial_id=7)
    class Repo:
        def get_by_id(self, id, session):
            return client
        def update(self, id, data, session):
            return client
    monkeypatch.setattr(cl, "client_repository", Repo())

    # User 7 (commercial), only own permission -> allowed on own
    _stub_token(monkeypatch, user_id=7, role_id=2)
    _stub_permissions(monkeypatch, {"client:update:own"})
    out = cl.client_logic.update_client("tok", user_id=7, client_id=1, client_data={"x": 1})
    assert out is client

    # User 8 (commercial), only own permission -> denied on others
    _stub_token(monkeypatch, user_id=8, role_id=2)
    _stub_permissions(monkeypatch, {"client:update:own"})
    with pytest.raises(PermissionError):
        cl.client_logic.update_client("tok", user_id=8, client_id=1, client_data={"x": 1})

    # Management with global client:update -> allowed partout
    _stub_token(monkeypatch, user_id=1, role_id=1)
    _stub_permissions(monkeypatch, {"client:update"})
    out = cl.client_logic.update_client("tok", user_id=1, client_id=1, client_data={"x": 1})
    assert out is client


def test_contract_update_own_vs_any(monkeypatch):
    contract = Contract(2, client_id=1, commercial_id=9)
    class Repo:
        def get_by_id(self, id, session):
            return contract
        def update(self, id, data, session):
            return contract
    monkeypatch.setattr(col, "contract_repository", Repo())

    # Owner (9) with own permission -> allowed
    _stub_token(monkeypatch, user_id=9, role_id=2)
    _stub_permissions(monkeypatch, {"contract:update:own"})
    out = col.contract_logic.update_contract("tok",
                                             user_id=9,
                                             contract_id=2,
                                             contract_data={"x": 1})
    assert out is contract

    # Non-owner denied with only own permission
    _stub_token(monkeypatch, user_id=10, role_id=2)
    _stub_permissions(monkeypatch, {"contract:update:own"})
    with pytest.raises(PermissionError):
        col.contract_logic.update_contract("tok",
                                            user_id=10,
                                            contract_id=2,
                                            contract_data={"x": 1})

    # Management global update allowed
    _stub_token(monkeypatch, user_id=1, role_id=1)
    _stub_permissions(monkeypatch, {"contract:update"})
    out = col.contract_logic.update_contract("tok",
                                            user_id=1,
                                            contract_id=2,
                                            contract_data={"x": 1})
    assert out is contract


def test_event_update_assigned_vs_any(monkeypatch):
    event = Event(3, contract_id=2, support_contact_id=15)
    class Repo:
        def get_by_id(self, id, session):
            return event
        def update(self, id, data, session):
            return event
    monkeypatch.setattr(el, "event_repository", Repo())

    # Support assigned, only assigned permission -> allowed
    _stub_token(monkeypatch, user_id=15, role_id=3)
    _stub_permissions(monkeypatch, {"event:update:assigned"})
    out = el.event_logic.update_event("tok", user_id=15, event_id=3, event_data={"title": "T"})
    assert out is event

    # Different support user -> denied
    _stub_token(monkeypatch, user_id=16, role_id=3)
    _stub_permissions(monkeypatch, {"event:update:assigned"})
    with pytest.raises(PermissionError):
        el.event_logic.update_event("tok", user_id=16, event_id=3, event_data={"title": "T"})

    # Management with event:update -> allowed
    _stub_token(monkeypatch, user_id=1, role_id=1)
    _stub_permissions(monkeypatch, {"event:update"})
    out = el.event_logic.update_event("tok", user_id=1, event_id=3, event_data={"title": "T"})
    assert out is event


def test_event_create_own_client_vs_any(monkeypatch):
    contract = Contract(4, client_id=1, commercial_id=20, is_signed=True)
    class CRepo:
        def get_by_id(self, id, session):
            return contract
    class ERepo:
        def create(self, data, session):
            return Event(5, contract_id=4)
    monkeypatch.setattr(el, "contract_repository", CRepo())
    monkeypatch.setattr(el, "event_repository", ERepo())

    # Commercial owner with own_client permission -> allowed
    _stub_token(monkeypatch, user_id=20, role_id=2)
    _stub_permissions(monkeypatch, {"event:create:own_client"})
    ev = el.event_logic.create_event("tok",
                                    {
                                        "contract_id": 4,
                                        "title": "A",
                                        "full_address": "X",
                                        "start_date": 0,
                                        "end_date": 1,
                                        "participant_count": 0
                                    }
                                    )
    assert isinstance(ev, Event)

    # Different commercial -> denied
    _stub_token(monkeypatch, user_id=21, role_id=2)
    _stub_permissions(monkeypatch, {"event:create:own_client"})
    with pytest.raises(PermissionError):
        el.event_logic.create_event("tok", {"contract_id": 4, "title": "A", "full_address": "X", "start_date": 0, "end_date": 1, "participant_count": 0})

    # Management with global event:create -> allowed
    _stub_token(monkeypatch, user_id=1, role_id=1)
    _stub_permissions(monkeypatch, {"event:create"})
    ev = el.event_logic.create_event("tok", {"contract_id": 4, "title": "A", "full_address": "X", "start_date": 0, "end_date": 1, "participant_count": 0})
    assert isinstance(ev, Event)

