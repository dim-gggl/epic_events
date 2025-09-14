import types

import src.views.views as views


def test_clear_console_decorator(monkeypatch):
    called = {"clear": 0, "fn": 0}
    monkeypatch.setattr(views, "clear", lambda: called.__setitem__("clear", called["clear"] + 1))

    @views.clear_console
    def fn():
        called["fn"] += 1
        return 42

    out = fn()
    assert out == 42
    assert called["clear"] == 1


def test_mainview_displayers_do_not_crash(monkeypatch):
    # Replace print to avoid actual console output
    monkeypatch.setattr(views, "print", lambda *a, **k: None)
    mv = views.MainView()

    # Minimal dummy objects with required attributes
    User = types.SimpleNamespace
    Client = types.SimpleNamespace
    Contract = types.SimpleNamespace
    Event = types.SimpleNamespace
    Company = types.SimpleNamespace

    mv.display_users([User(id=1, username="u", role_id=1)])
    mv.display_user(User(id=1, username="u", full_name="U", email="a@b", role_id=1, is_active=True, created_at=0, updated_at=0, last_login=0))

    mv.display_list_clients([Client(id=1, full_name="C", commercial_id=1)])
    mv.display_client_detail("tok", Client(id=1, full_name="C", email="a@b", phone="+33", company_id=1, commercial_id=1, first_contact_date=0, last_contact_date=0))

    mv.display_contracts([Contract(id=1, client_id=1, commercial_id=1, total_amount=10, is_signed=True, is_fully_paid=False)])
    mv.display_contract(Contract(id=1, title="T", client_id=1, commercial_id=1, total_amount=10, remaining_amount=5, is_signed=True, is_fully_paid=False, created_at=0, updated_at=0))

    mv.display_events([Event(id=1, title="E", start_date=types.SimpleNamespace(strftime=lambda f: "01/01/2020"), support_contact_id=1)])
    mv.display_event(Event(id=1, title="E", contract_id=1, support_contact_id=1, start_date=0, end_date=0, participant_count=0, full_address="A", notes="N"))


