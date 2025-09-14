import importlib

import pytest

import src.auth.utils as utils


def test_get_secret_key_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        utils.get_secret_key()


def test_get_secret_key_present(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "abc")
    assert utils.get_secret_key() == "abc"


def test_prompt_password_success(monkeypatch):
    # Stub console input to supply password and confirmation
    class FakeConsole:
        def __init__(self):
            self.calls = []
        def input(self, prompt: str, password: bool = False):
            self.calls.append(prompt)
            # First call: password; Second: confirmation
            return "Abcdefg1"

    fake_console = FakeConsole()
    monkeypatch.setattr(utils, "console", fake_console)
    monkeypatch.setattr(utils, "is_valid_password", lambda p: True)

    assert utils._prompt_password() == "Abcdefg1"


def test_prompt_password_mismatch_returns_none(monkeypatch, dummy_view):
    class FakeConsole:
        def __init__(self, values):
            self.values = list(values)
        def input(self, prompt: str, password: bool = False):
            return self.values.pop(0)

    fake_console = FakeConsole(["Abcdefg1", "Different1"])  # pw, confirm
    monkeypatch.setattr(utils, "console", fake_console)
    monkeypatch.setattr(utils, "is_valid_password", lambda p: True)
    monkeypatch.setattr(utils, "view", dummy_view)

    assert utils._prompt_password() is None


def test_prompt_password_invalid_then_retry(monkeypatch, dummy_view):
    # First attempt invalid, second attempt valid and confirmed
    class FakeConsole:
        def __init__(self, values):
            self.values = list(values)
        def input(self, prompt: str, password: bool = False):
            return self.values.pop(0)

    # Sequence: invalid password (ignored), then valid pwd and confirm
    fake_console = FakeConsole(["weak", "Strong1Pass", "Strong1Pass"]) 
    def validate(p):
        return p != "weak"

    monkeypatch.setattr(utils, "console", fake_console)
    monkeypatch.setattr(utils, "is_valid_password", validate)
    monkeypatch.setattr(utils, "view", dummy_view)

    assert utils._prompt_password() == "Strong1Pass"


