
import src.sentry.observability as obs


def test_init_sentry_calls_sdk(monkeypatch):
    called = {"args": None, "kwargs": None}
    def fake_init(*a, **k):
        called["args"] = a
        called["kwargs"] = k
    monkeypatch.setattr(obs.sentry_sdk, "init", fake_init)

    monkeypatch.setenv("SENTRY_DSN", "http://example")
    obs.init_sentry()

    assert called["kwargs"]["dsn"] == "http://example"
    assert called["kwargs"]["traces_sample_rate"] == 1.0
    assert called["kwargs"]["profile_session_sample_rate"] == 1.0
    assert called["kwargs"]["enable_logs"] is True



