from click.testing import CliRunner

import src.cli.main as cli


def _run(cmd):
    runner = CliRunner()
    return runner.invoke(cli.cli, cmd)


def test_smoke_login_handles_exception(monkeypatch):
    class MC:
        def login(self, u, p):
            raise RuntimeError("boom")
    monkeypatch.setattr(cli, "main_controller", MC())

    res = _run(["login", "-u", "john"])
    assert res.exit_code == 0
    assert "Login" in res.output  # title present in panel


def test_smoke_role_list_permission_error(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    class RL:
        def list_roles(self, token):
            raise PermissionError("nope")
    monkeypatch.setattr(cli, "role_logic", RL())

    res = _run(["role", "list"])
    assert res.exit_code == 0
    assert "Permission" in res.output


def test_smoke_event_create_permission_error(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    class MC:
        def create_event(self, *a, **k):
            raise PermissionError("denied")
    monkeypatch.setattr(cli, "main_controller", MC())

    res = _run(["event", "create", "--title", "T"])
    assert res.exit_code == 0
    assert "Event Create" in res.output


def test_smoke_company_update_handles_error(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    class MC:
        def update_company(self, *a, **k):
            raise ValueError("bad")
    monkeypatch.setattr(cli, "main_controller", MC())

    res = _run(["company", "update", "99", "-n", "X"])
    assert res.exit_code == 0
    assert "Company Update" in res.output

