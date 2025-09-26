import phonenumbers
from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select

from src.auth.settings import (
    PASSWORD_MAX_LENGTH as pwd_max_lgt,
)
from src.auth.settings import (
    PASSWORD_MIN_LENGTH as pwd_min_lgt,
)
from src.auth.settings import (
    ROLE_MAX_ID as role_id_max,
)
from src.auth.settings import (
    ROLE_MIN_ID as role_id_min,
)
from src.auth.settings import (
    USERNAME_MAX_LENGTH as username_max_lgt,
)
from src.auth.settings import (
    USERNAME_MIN_LENGTH as username_min_lgt,
)
from src.crm.models import User, Client
from src.data_access.config import Session

__all__ = ["is_valid_email", "is_valid_username", "is_valid_password",
           "is_valid_role_id", "is_valid_phone", "is_email_globally_unique",
           "is_phone_globally_unique", "is_username_globally_unique"]


def is_valid_email(value: str) -> bool:
    """Validate an email address."""
    try:
        validate_email(value, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _validate_username_length(username: str) -> bool:
    """Validate that a username is between 5 and 64 characters long."""
    return  username_min_lgt <= len(username) <= username_max_lgt


def _validate_username_uniqueness(username: str) -> bool:
    """Validate that a username is not already in the database."""
    with Session() as session:
        return not session.scalar(
            select(User).filter(User.username == username)
        )


def is_valid_username(username: str) -> bool:
    """Validate that a username is valid and not already in use."""
    return _validate_username_length(username) and \
                _validate_username_uniqueness(username)


def _validate_password_length(password: str) -> bool:
    """Validate that a password is between min and max characters long."""
    return bool(len(password) >= pwd_min_lgt and
                len(password) <= pwd_max_lgt)


def _validate_password_complexity(password: str) -> bool:
    """
    Validate that a password contains at least one uppercase letter, 
    one lowercase letter and one digit.
    """
    return bool(
        any(char.isupper() for char in password) and
        any(char.islower() for char in password) and
        any(char.isdigit() for char in password)
    )


def is_valid_password(password: str) -> bool:
    """Validate that a password meets all requirements."""
    return bool(_validate_password_length(password) and
                _validate_password_complexity(password))


def is_valid_role_id(role_id: int) -> bool:
    """Validate that a role id is within valid range."""
    return role_id_min <= int(role_id) <= role_id_max


def is_valid_phone(phone: str) -> bool:
    """Validate phone number using phonenumbers library."""
    if not phone:
        return False

    normalized = phone.strip()
    if normalized.startswith("00"):
        normalized = "+" + normalized[2:]
    elif normalized.startswith("0"):
        normalized = "+33" + normalized[1:]
    elif not normalized.startswith("+"):
        normalized = "+" + normalized

    try:
        parsed = phonenumbers.parse(normalized)
    except Exception as e:
        print(e)
        return False
    return phonenumbers.is_valid_number(parsed)


# Global uniqueness validators across all entities

def is_email_globally_unique(email: str, exclude_user_id: int = None, exclude_client_id: int = None) -> bool:
    """Validate that an email is not already used by any User or Client."""
    with Session() as session:
        # Check Users table
        user_query = select(User).filter(User.email == email)
        if exclude_user_id:
            user_query = user_query.filter(User.id != exclude_user_id)
        if session.scalar(user_query):
            return False

        # Check Clients table
        client_query = select(Client).filter(Client.email == email)
        if exclude_client_id:
            client_query = client_query.filter(Client.id != exclude_client_id)
        if session.scalar(client_query):
            return False

        return True


def is_phone_globally_unique(phone: str, exclude_client_id: int = None) -> bool:
    """Validate that a phone number is not already used by any Client."""
    if not phone:
        return True  # Empty phone is allowed

    with Session() as session:
        query = select(Client).filter(Client.phone == phone)
        if exclude_client_id:
            query = query.filter(Client.id != exclude_client_id)
        return not session.scalar(query)


def is_username_globally_unique(username: str, exclude_user_id: int = None) -> bool:
    """Validate that a username is not already used by any User."""
    with Session() as session:
        query = select(User).filter(User.username == username)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return not session.scalar(query)
