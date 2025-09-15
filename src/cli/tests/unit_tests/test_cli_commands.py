from click.testing import CliRunner

import src.cli.main as cli


def test_root_invokes_help(monkeypatch):
    printed = {"calls": 0}
    def fake_render(ctx):
        printed["calls"] += 1
    monkeypatch.setattr(cli, "render_help_with_logo", fake_render)

    runner = CliRunner()
    result = runner.invoke(cli.cli, [])
    assert result.exit_code == 0
    assert printed["calls"] == 1


def test_get_required_token_prompts_login(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: None)
    messages = []
    monkeypatch.setattr(cli, "print", lambda *a, **k: messages.append(a[0]))
    assert cli.get_required_token() is None
    assert "Please login first" in messages[0]


def test_user_list_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    called = {}
    class MC:
        def list_users(self, token, m, c, s):
            called["v"] = (token, m, c, s)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["user", "list", "--management"])
    assert result.exit_code == 0
    assert called["v"] == ("tok", True, False, False)


def test_client_create_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    called = {"v": None}
    class MC:
        def create_client(self, *args, **kwargs):
            called["v"] = (args, kwargs)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["client", "create", "-n", "A", "-e", "a@b", "-p", "+33600000000"])
    assert result.exit_code == 0
    assert called["v"][0][0] == "tok"


def test_help_command_for_specific_subcommand(monkeypatch):
    calls = {"count": 0, "names": []}
    def fake_render(ctx):
        calls["count"] += 1
        calls["names"].append(ctx.command.name)
    monkeypatch.setattr(cli, "render_help_with_logo", fake_render)

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["help", "user"])
    assert result.exit_code == 0
    # Should render help for the specific subcommand once
    assert calls["count"] == 1
    assert calls["names"][0] == "user"


def test_help_command_unknown_subcommand(monkeypatch):
    calls = {"count": 0}
    monkeypatch.setattr(cli, "render_help_with_logo", lambda ctx: calls.__setitem__("count", calls["count"] + 1))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["help", "unknowncmd"])
    assert result.exit_code == 0
    assert "Unknown command: unknowncmd" in result.output
    # Help should still render once for the parent group
    assert calls["count"] == 1


def test_login_calls_controller(monkeypatch):
    captured = {"args": None}
    class MC:
        def login(self, u, p):
            captured["args"] = (u, p)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["login", "-u", "user1", "-p", "pwd"])
    assert result.exit_code == 0
    assert captured["args"] == ("user1", "pwd")


def test_logout_calls_controller(monkeypatch):
    called = {"v": 0}
    class MC:
        def logout(self):
            called["v"] += 1
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["logout"])
    assert result.exit_code == 0
    assert called["v"] == 1


def test_db_create_calls_init_db(monkeypatch):
    called = {"v": 0}
    monkeypatch.setattr(cli, "init_db", lambda: called.__setitem__("v", called["v"] + 1))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["db-create"])
    assert result.exit_code == 0
    assert called["v"] == 1


def test_manager_create_calls_init_manager(monkeypatch):
    captured = {"args": None}
    monkeypatch.setattr(cli, "init_manager", lambda u, n, e: captured.__setitem__("args", (u, n, e)))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["manager-create", "-u", "mgr", "-n", "Boss", "-e", "b@c"])
    assert result.exit_code == 0
    assert captured["args"] == ("mgr", "Boss", "b@c")


def test_user_create_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    called = {"v": 0}
    class MC:
        def create_user(self, token):
            assert token == "tok"
            called["v"] += 1
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["user", "create"])
    assert result.exit_code == 0
    assert called["v"] == 1


def test_user_view_update_delete_call_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    captured = {"view": None, "update": None, "delete": None}
    class MC:
        def view_user(self, token, user_id):
            captured["view"] = (token, user_id)
        def update_user(self, token, user_id):
            captured["update"] = (token, user_id)
        def delete_user(self, token, user_id):
            captured["delete"] = (token, user_id)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    assert runner.invoke(cli.cli, ["user", "view", "5"]).exit_code == 0
    assert runner.invoke(cli.cli, ["user", "update", "6"]).exit_code == 0
    assert runner.invoke(cli.cli, ["user", "delete", "7"]).exit_code == 0
    assert captured["view"] == ("tok", 5)
    assert captured["update"] == ("tok", 6)
    assert captured["delete"] == ("tok", 7)


def test_client_list_only_mine_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    captured = {"args": None}
    class MC:
        def list_clients(self, token, only_mine):
            captured["args"] = (token, only_mine)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["client", "list", "--only-mine"])
    assert result.exit_code == 0
    assert captured["args"] == ("tok", True)


def test_contract_create_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    captured = {"args": None}
    class MC:
        def create_contract(self, token, client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid):
            captured["args"] = (token, client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid)
    monkeypatch.setattr(cli, "main_controller", MC())

    args = [
        "contract", "create",
        "--client-id", "100",
        "--commercial-id", "200",
        "--total-amount", "123.45",
        "--remaining-amount", "23.45",
        "--is-signed", "true",
        "--is-fully-paid", "false",
    ]
    runner = CliRunner()
    result = runner.invoke(cli.cli, args)
    assert result.exit_code == 0
    assert captured["args"] == ("tok", "100", "200", "123.45", "23.45", "true", "false")


def test_contract_list_view_update_delete_calls_controller(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    captured = {"list": None, "view": None, "update": None, "delete": None}
    class MC:
        def list_contracts(self, token, only_mine, *rest):
            captured["list"] = (token, only_mine)
        def view_contract(self, token, cid):
            captured["view"] = (token, cid)
        def update_contract(self, token, cid, *rest):
            captured["update"] = (token, cid)
        def delete_contract(self, token, cid):
            captured["delete"] = (token, cid)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    assert runner.invoke(cli.cli, ["contract", "list", "--only-mine"]).exit_code == 0
    assert runner.invoke(cli.cli, ["contract", "view", "13"]).exit_code == 0
    assert runner.invoke(cli.cli, ["contract", "update", "14"]).exit_code == 0
    assert runner.invoke(cli.cli, ["contract", "delete", "15"]).exit_code == 0
    assert captured["list"] == ("tok", True)
    assert captured["view"] == ("tok", 13)
    assert captured["update"] == ("tok", 14)
    assert captured["delete"] == ("tok", 15)


def test_event_create_list_view_update_assign_delete(monkeypatch):
    monkeypatch.setattr(cli, "get_access_token", lambda: "tok")
    captured = {"create": 0, "list": None, "view": None, "update": None, "assign": None, "delete": None}
    class MC:
        def create_event(self, token, *rest):
            assert token == "tok"
            captured["create"] += 1
        def list_events(self, token, only_mine, *rest):
            captured["list"] = (token, only_mine)
        def view_event(self, token, eid):
            captured["view"] = (token, eid)
        def update_event(self, token, eid, *rest):
            captured["update"] = (token, eid)
        def assign_support_to_event(self, token, eid, sid):
            captured["assign"] = (token, eid, sid)
        def delete_event(self, token, eid):
            captured["delete"] = (token, eid)
    monkeypatch.setattr(cli, "main_controller", MC())

    runner = CliRunner()
    assert runner.invoke(cli.cli, ["event", "create"]).exit_code == 0
   

