import pytest

import src.data_access.create_tables as ct


def test_database_has_any_data_false(monkeypatch):
    class Insp:
        def get_table_names(self):
            return []
    monkeypatch.setattr(ct, "inspect", lambda *a, **k: Insp())
    assert ct._database_has_any_data() is False


def test_init_db_aborts_if_has_data(monkeypatch):
    monkeypatch.setattr(ct, "_database_has_any_data", lambda: True)
    with pytest.raises(RuntimeError):
        ct.init_db()


def test_init_db_calls_create_and_seed(monkeypatch):
    called = {"create": False, "seed": False, "commit": False}
    class DummyMeta:
        def create_all(self, engine):
            called["create"] = True
    class DummySession:
        def __call__(self):
            return self
        def commit(self):
            called["commit"] = True
        def close(self):
            pass
    monkeypatch.setattr(ct, "_database_has_any_data", lambda: False)
    monkeypatch.setattr(ct, "metadata", DummyMeta())
    monkeypatch.setattr(ct, "Session", DummySession())
    def seed(session):
        called["seed"] = True
    monkeypatch.setattr(ct, "_seed_roles", seed)

    ct.init_db()
    assert called["create"] and called["seed"] and called["commit"]


