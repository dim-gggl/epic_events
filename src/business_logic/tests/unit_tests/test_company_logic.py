import pytest

import src.business_logic.company_logic as col


class DummyCompany:
    def __init__(self, id=1):
        self.id = id
        self.clients = []


def test_create_company(monkeypatch, make_session):
    class Repo:
        def create(self, data, session):
            return DummyCompany(2)
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "company_repository", Repo())

    company = col.company_logic.create_company("tok", {"name": "ACME"})
    assert isinstance(company, DummyCompany)


def test_get_companies(monkeypatch, make_session):
    class Repo:
        def get_all(self, session):
            return [DummyCompany(1), DummyCompany(2)]
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "company_repository", Repo())

    companies = col.company_logic.get_companies("tok")
    assert len(companies) == 2


def test_get_company_by_id(monkeypatch, make_session):
    # Using session.query path exercised by logic
    dummy = DummyCompany(3)
    monkeypatch.setattr(col, "Session", lambda: make_session(query_first=dummy))
    c = col.company_logic.get_company_by_id("tok", 3)
    assert c is dummy


def test_update_company_absent_returns_none(monkeypatch, make_session):
    class Repo:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "company_repository", Repo())
    assert col.company_logic.update_company("tok", 1, {"name": "X"}) is None


def test_update_company_success(monkeypatch, make_session):
    c = DummyCompany(4)
    class Repo:
        def get_by_id(self, id, session):
            return c
        def update(self, id, data, session):
            return c
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "company_repository", Repo())
    assert col.company_logic.update_company("tok", 4, {"name": "Y"}) is c


def test_delete_company_rules(monkeypatch, make_session):
    # Not found
    class Repo1:
        def get_by_id(self, id, session):
            return None
    monkeypatch.setattr(col, "Session", lambda: make_session())
    monkeypatch.setattr(col, "company_repository", Repo1())
    assert col.company_logic.delete_company("tok", 1) is None

    # With clients -> raises
    with_clients = DummyCompany(2)
    with_clients.clients = [object()]
    class Repo2:
        def get_by_id(self, id, session):
            return with_clients
    monkeypatch.setattr(col, "company_repository", Repo2())
    with pytest.raises(ValueError):
        col.company_logic.delete_company("tok", 2)

    # Success delete
    class Repo3:
        def get_by_id(self, id, session):
            return DummyCompany(3)
        def delete(self, id, session):
            return True
    monkeypatch.setattr(col, "company_repository", Repo3())
    assert col.company_logic.delete_company("tok", 3) is True


