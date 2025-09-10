from email_validator import validate_email, EmailNotValidError
from src.data_access.config import Session
from src.crm.models import User
from sqlalchemy import select
import phonenumbers

# Constants
USERNAME_MIN_LENGTH = 5
USERNAME_MAX_LENGTH = 64
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
ROLE_MIN_ID = 1
ROLE_MAX_ID = 3


__all__ = ["is_valid_email", "is_valid_username", "is_valid_password", 
           "is_valid_role_id", "is_valid_phone"]


def is_valid_email(value: str) -> bool:
    """Validate an email address."""
    try:
        validate_email(value, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _validate_username_length(username: str) -> bool:
    """Validate that a username is between 5 and 64 characters long."""
    return  5 <= len(username) <= 64


def _validate_username_uniqueness(username: str) -> bool:
    """Validate that a username is not already in the database."""
    with Session() as session:
        return not session.scalar(
            select(User).where(User.username == username).one_or_none()
        )


def is_valid_username(username: str) -> bool:
    """Validate that a username is valid and not already in use."""
    return bool(_validate_username_length(username) and 
                _validate_username_uniqueness(username))


def _validate_password_length(password: str) -> bool:
    """Validate that a password is between min and max characters long."""
    return bool(len(password) >= PASSWORD_MIN_LENGTH and 
                len(password) <= PASSWORD_MAX_LENGTH)


def _validate_password_complexity(password: str) -> bool:
    """
    Validate that a password contains at least one uppercase letter, 
    one lowercase letter and one digit.
    """
    return bool(
        any(char.isupper() for char in password) and
        any(char.islower() for char in password) and
        any(char.isalpha() for char in password) and
        any(char.isdigit() for char in password)
    )


def is_valid_password(password: str) -> bool:
    """Validate that a password meets all requirements."""
    return bool(_validate_password_length(password) and 
                _validate_password_complexity(password))


def is_valid_role_id(role_id: int) -> bool:
    """Validate that a role id is within valid range."""
    return ROLE_MIN_ID <= role_id <= ROLE_MAX_ID


def is_valid_phone(phone: str) -> bool:
    """Validate phone number using phonenumbers library."""
    try:
        return phonenumbers.is_valid_number(phonenumbers.parse(phone))
    except Exception as e:
        raise e