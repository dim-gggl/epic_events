import epic_events as app


def test_main_invokes_cli(monkeypatch):
    called = {"v": False, "sentry": False}
    monkeypatch.setattr(app, "cli", lambda: called.__setitem__("v", True))
    monkeypatch.setattr(app, "init_sentry", lambda: called.__setitem__("sentry", True))
    app.main()
    assert called["sentry"] is True
    assert called["v"] is True


