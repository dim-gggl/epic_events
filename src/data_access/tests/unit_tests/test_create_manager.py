import types

import src.data_access.create_manager as cm


def test_ensure_root_posix_denied(monkeypatch):
    monkeypatch.setattr(cm.os, "name", "posix")
    monkeypatch.setattr(cm.os, "geteuid", lambda: 1000)
    msgs = []
    monkeypatch.setattr(cm.sys, "stderr", types.SimpleNamespace(write=lambda m: msgs.append(m)))
    cm._ensure_root()
    assert "root" in msgs[0]


def test_init_manager_non_interactive(monkeypatch):
    # Pretend already root and valid inputs provided
    monkeypatch.setattr(cm, "_ensure_root", lambda: None)
    called = {"committed": False}

    class Role:
        id = 1
        name = "management"

    class DummySession:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def scalar(self, stmt):
            # Return None for role -> so it creates role
            return None if "Role" in repr(stmt) else None
        def add(self, obj):
            pass
        def flush(self):
            pass
        def commit(self):
            called["committed"] = True

    monkeypatch.setattr(cm, "Session", lambda: DummySession())
    monkeypatch.setattr(cm, "hash_password", lambda p: "hashed")
    monkeypatch.setattr(cm, "_prompt_password", lambda **k: "Abcdefg1")
    # Bypass email/username validators
    monkeypatch.setattr(cm, "is_valid_username", lambda u: True)
    monkeypatch.setattr(cm, "is_valid_email", lambda e: True)

    cm.init_manager(username="adminuser", full_name="Admin User", email="a@b")
    assert called["committed"] is True


