from email_validator import validate_email, EmailNotValidError


def is_valid_email(value: str) -> bool:
    """Validate an email address"""
    try:
        validate_email(value, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def _validate_username_length(username: str) -> bool:
    """Validate that a username is between 5 and 64 characters long."""
    return bool(len(username) >= 5 and len(username) <= 64)

def _validate_username_uniqueness(username: str, usernames: list[str]) -> bool:
    """Validate that a username is not already in the list."""
    return username not in usernames

def is_valid_username(username: str, usernames: list[str]) -> bool:
    """Validate that a username is valid and not already in the list."""
    return bool(_validate_username_length(username) and \
        _validate_username_uniqueness(username, usernames))

def _validate_password_length(password: str) -> bool:
    """Validate that a password is between 8 and 128 characters long."""
    return bool(len(password) >= 8 and len(password) <= 128)

def _validate_password_complexity(password: str) -> bool:
    """
    Validate that a password contains at least one uppercase letter, 
    one lowercase letter and one digit.
    """
    return bool(
        any(
            char.isupper() for char in password
        ) and any(
            char.islower() for char in password
        ) and any(
            char.isalpha() for char in password
        ) and any(
            char.isdigit() for char in password
        )
    )

def is_valid_password(password: str) -> bool:
    """Validate that a password is valid."""
    return bool(_validate_password_length(password) and \
        _validate_password_complexity(password))
