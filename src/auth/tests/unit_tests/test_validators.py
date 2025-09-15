import pytest

from src.auth.validators import (
    is_valid_email,
    is_valid_password,
    is_valid_phone,
    is_valid_role_id,
    is_valid_username,
)


def test_is_valid_email():
    assert is_valid_email("john.doe@example.com") is True
    assert is_valid_email("bad@") is False


def test_is_valid_username_length_only(monkeypatch):
    # Force uniqueness check to True to isolate length behavior
    import src.auth.validators as validators
    monkeypatch.setattr(validators, "_validate_username_uniqueness", lambda u: True)

    assert is_valid_username("abcde") is True
    assert is_valid_username("abcd") is False
    assert is_valid_username("a" * 64) is True
    assert is_valid_username("a" * 65) is False


def test_is_valid_password():
    assert is_valid_password("Abcdefg1") is True
    # Too short
    assert is_valid_password("Abcde1") is False
    # Missing digit
    assert is_valid_password("Abcdefgh") is False
    # Missing uppercase
    assert is_valid_password("abcdefg1") is False
    # Missing lowercase
    assert is_valid_password("ABCDEFG1") is False


@pytest.mark.parametrize("role_id, expected", [
    (1, True), (2, True), (3, True), (0, False), (4, False)
])
def test_is_valid_role_id(role_id, expected):
    assert is_valid_role_id(role_id) is expected


@pytest.mark.parametrize("phone, valid", [
    ("+33612345678", True),
    ("0612345678", True),
    ("0033612345678", True),
    ("612345678", False),
])
def test_is_valid_phone(phone, valid):
    assert is_valid_phone(phone) is valid


