import importlib
import os
import sys

import pytest

# Ensure SECRET_KEY is present for any import-time usage in modules
os.environ.setdefault("SECRET_KEY", "test-secret")

# Ensure repository root is importable so `import src...` works
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class DummyView:
    """Simple dummy view to capture messages without side effects."""

    def __init__(self) -> None:
        self.messages = []

    def wrong_message(self, message: str) -> None:
        self.messages.append(("wrong", message))

    def success_message(self, message: str) -> None:
        self.messages.append(("success", message))

    def display_message(self, message: str) -> None:
        self.messages.append(("display", message))

    def display_login(self, *args, **kwargs) -> None:
        self.messages.append(("display_login", args))

    def get_messages(self):
        return self.messages


@pytest.fixture(autouse=True)
def set_env_and_reload_jwt(monkeypatch):
    """Ensure SECRET_KEY is set and JWT modules pick it up at runtime."""
    monkeypatch.setenv("SECRET_KEY", os.environ.get("SECRET_KEY", "test-secret"))
    # Reload modules that cache SECRET_KEY at import time
    try:
        import src.auth.jwt.config as jwt_config
        import src.auth.jwt.verify_token as verify_token
        importlib.reload(jwt_config)
        importlib.reload(verify_token)
    except Exception:
        # Tests that don't touch JWT shouldn't fail due to missing imports
        pass


@pytest.fixture()
def dummy_view() -> DummyView:
    return DummyView()


@pytest.fixture()
def isolated_token_file(monkeypatch, tmp_path, dummy_view):
    """Route token storage to a temporary file and stub the view.

    Yields the path used for the token file.
    """
    import src.auth.jwt.token_storage as token_storage

    token_file = tmp_path / "session.jwt"

    def fake_get_auth_location() -> str:
        return str(token_file)

    monkeypatch.setattr(token_storage, "_get_auth_location", fake_get_auth_location)
    monkeypatch.setattr(token_storage, "view", dummy_view)

    yield str(token_file)

    # Cleanup at the end just in case
    try:
        if os.path.exists(token_file):
            os.remove(token_file)
    except Exception:
        pass


