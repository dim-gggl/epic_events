"""
Common utilities and helper functions for the Epic Events CRM application.
"""

from typing import Any, Optional, Callable, Type, Union
from functools import wraps
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

from db.config import Session as DBSession
from auth.jwt.verify_token import verify_access_token
from crm.views.views import MainView
from constants import *


view = MainView()


def get_user_id_from_token(access_token: str) -> int:
    """Extract user ID from access token."""
    payload = verify_access_token(access_token)
    return int(payload["sub"])


def get_role_id_from_token(access_token: str) -> int:
    """Extract role ID from access token."""
    payload = verify_access_token(access_token)
    return int(payload["role_id"])


def check_object_exists(session: Session, model_class: Type, obj_id: int) -> Optional[Any]:
    """Check if an object exists in the database."""
    return session.scalars(
        select(model_class).filter(model_class.id == obj_id)
    ).one_or_none()


def check_associated_records(session: Session, model_class: Type, 
                           foreign_key_field: str, obj_id: int) -> bool:
    """Check if an object has associated records."""
    query = select(model_class).filter(getattr(model_class, foreign_key_field) == obj_id)
    return bool(session.scalars(query).first())


def format_currency(amount: Union[int, float]) -> str:
    """Format amount as currency."""
    return f"{amount}€"


def format_date(date: datetime) -> str:
    """Format date using common format."""
    return date.strftime(DATE_FORMAT)


def format_datetime(dt: datetime) -> str:
    """Format datetime using common format."""
    return dt.strftime(f"{DATE_FORMAT} %H:%M")


def format_boolean(value: bool) -> str:
    """Format boolean as Yes/No."""
    return "Yes" if value else "No"


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object."""
    return getattr(obj, attr, default)


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def validate_required_fields(data: dict, required_fields: list) -> Optional[str]:
    """Validate that all required fields are present and not empty."""
    for field in required_fields:
        if field not in data or not data[field]:
            return f"{field.replace('_', ' ').title()} {REQUIRED_FIELD}"
    return None


def create_error_message(operation: str, resource: str, reason: str = "") -> str:
    """Create standardized error message."""
    base_msg = f"{OPERATION_DENIED}: {operation} {resource} {NOT_FOUND}"
    if reason:
        base_msg += f" - {reason}"
    return base_msg


def create_success_message(operation: str, resource: str, details: str = "") -> str:
    """Create standardized success message."""
    base_msg = f"{resource} {operation} successfully"
    if details:
        base_msg += f" - {details}"
    return base_msg


def handle_database_operation(operation_func: Callable, *args, **kwargs) -> Any:
    """Handle database operations with common error handling."""
    try:
        with DBSession() as session:
            return operation_func(session, *args, **kwargs)
    except Exception as e:
        view.wrong_message(f"Database operation failed: {str(e)}")
        return None


def validate_date_string(date_str: str) -> Optional[datetime]:
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        return None


def validate_yes_no_input(input_str: str) -> Optional[bool]:
    """Validate yes/no input."""
    input_str = input_str.strip().lower()
    if input_str in {"y", "yes"}:
        return True
    elif input_str in {"n", "no"}:
        return False
    return None


def validate_positive_number(value: Union[str, int, float]) -> Optional[float]:
    """Validate positive number."""
    try:
        num = float(value)
        return num if num >= 0 else None
    except (ValueError, TypeError):
        return None


def validate_integer(value: Union[str, int]) -> Optional[int]:
    """Validate integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def create_table_row(*values: str, styles: list = None) -> list:
    """Create a table row with optional styles."""
    if styles is None:
        styles = [TABLE_STYLE_CONTENT] * len(values)
    
    from rich.text import Text
    return [Text(str(val), style=style) for val, style in zip(values, styles)]


def create_table_header(*headers: str, style: str = TABLE_STYLE_HEADER) -> list:
    """Create table headers with consistent styling."""
    from rich.text import Text
    return [Text(header, style=style) for header in headers]


def format_object_id(obj_id: Union[int, str, None]) -> str:
    """Format object ID for display."""
    if obj_id is None:
        return "Not assigned"
    return str(obj_id)


def get_role_name(role_id: int) -> str:
    """Get role name from role ID."""
    return ROLE_NAMES.get(role_id, f"Role {role_id}")


def check_permission_for_own_record(access_token: str, record_owner_id: int) -> bool:
    """Check if user can access their own record."""
    current_user_id = get_user_id_from_token(access_token)
    return current_user_id == record_owner_id


def create_permission_error_message(operation: str, resource: str) -> str:
    """Create permission denied error message."""
    return f"{OPERATION_DENIED}: {PERMISSION_DENIED} {operation} {resource}"


def create_not_found_error_message(resource: str) -> str:
    """Create not found error message."""
    return f"{OPERATION_DENIED}: {resource.title()} {NOT_FOUND}"


def create_validation_error_message(field: str, reason: str) -> str:
    """Create validation error message."""
    return f"Invalid {field}: {reason}"


def create_required_field_error_message(field: str) -> str:
    """Create required field error message."""
    return f"{field.replace('_', ' ').title()} {REQUIRED_FIELD}"


def create_success_operation_message(operation: str, resource: str, 
                                   resource_name: str = "") -> str:
    """Create success operation message."""
    if resource_name:
        return f"{resource.title()} '{resource_name}' {operation} successfully"
    return f"{resource.title()} {operation} successfully"