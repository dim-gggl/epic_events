import os
import sys
import pytest


os.environ.setdefault("SECRET_KEY", "test-secret")

CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture(autouse=True)
def no_clear_console(monkeypatch):
    # Prevent clearing terminal during tests
    import src.views.views as views
    monkeypatch.setattr(views, "clear", lambda: None)


