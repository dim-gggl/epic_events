import pytest

import src.controllers.main_controller as mc


def test_to_int_and_float_and_bool_and_date():
    assert mc._to_int("42") == 42
    assert mc._to_float("1,5") == 1.5
    assert mc._to_bool_yes_no("yes") is True
    assert mc._to_bool_yes_no("no") is False
    with pytest.raises(ValueError):
        mc._to_bool_yes_no("maybe")
    d = mc._to_date("01/01/2020")
    assert d.year == 2020


def test_ask_and_ask_optional(monkeypatch):
    calls = {"n": 0}
    def prompt():
        calls["n"] += 1
        return "  5  " if calls["n"] > 1 else ""

    # ask: empty -> wrong_message -> then success
    msgs = []
    monkeypatch.setattr(mc, "view", type("V", (), {"wrong_message": lambda self, m: msgs.append(m)})())
    out = mc._ask(prompt, cast=int, required_msg="req")
    assert out == 5
    assert "req" in msgs[0]

    # ask_optional: empty -> None
    def p2():
        return ""
    assert mc._ask_optional(p2, cast=int) is None


