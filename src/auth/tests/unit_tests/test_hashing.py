import re

from src.auth.hashing import hash_password, verify_password


def test_hash_password_produces_different_hashes_for_same_input():
    # Given
    password = "StrongPass1"

    # When
    h1 = hash_password(password)
    h2 = hash_password(password)

    # Then
    assert isinstance(h1, str)
    assert isinstance(h2, str)
    assert h1 != h2
    # bcrypt hash format starts with $2b$ or $2a$
    assert re.match(r"^\$2[aby]\$\d{2}\$", h1)


def test_verify_password_success_and_failure():
    # Given
    password = "StrongPass1"
    wrong = "WrongPass1"
    password_hash = hash_password(password)

    # Then
    assert verify_password(password, password_hash) is True
    assert verify_password(wrong, password_hash) is False


