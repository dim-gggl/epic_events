import importlib


def test_build_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h:5432/d")
    cfg = importlib.import_module("src.data_access.config")
    assert cfg._build_url() == "postgresql+psycopg2://u:p@h:5432/d"


def test_build_url_composed_requires_password(monkeypatch):
    cfg = importlib.import_module("src.data_access.config")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    try:
        cfg._build_url()
        raised = False
    except ValueError:
        raised = True
    assert raised is True


def test_session_and_engine_exist(monkeypatch):
    cfg = importlib.import_module("src.data_access.config")
    assert hasattr(cfg, "engine")
    assert hasattr(cfg, "Session")


