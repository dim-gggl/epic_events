import os
import sys
import importlib
from types import SimpleNamespace

import pytest


# Ensure SECRET_KEY for any import-time usage in modules relying on it
os.environ.setdefault("SECRET_KEY", "test-secret")

# Ensure repository root in sys.path so `import src...` works during tests
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class DummySession:
    def __init__(self, query_first=None):
        self._committed = False
        self._refreshed = []
        self._query_first = query_first

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self._committed = True

    def refresh(self, obj):
        self._refreshed.append(obj)

    def query(self, model):
        class _Q:
            def __init__(self, first):
                self._first = first
            def options(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return self._first
        return _Q(self._query_first)


@pytest.fixture(autouse=True)
def relax_permissions(monkeypatch):
    import src.auth.permissions as perms
    # Allow all permissions and bypass token verification by default
    monkeypatch.setattr(perms, "has_permission", lambda tok, perm: True)
    monkeypatch.setattr(perms, 
                        "verify_access_token", 
                        lambda tok: {"sub": "1", "role_id": "1"})
    yield


@pytest.fixture()
def make_session():
    def _factory(query_first=None):
        return DummySession(query_first=query_first)
    return _factory
