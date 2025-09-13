import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
from sentry_sdk import init as sentry_init 
from sentry_sdk import capture_exception, capture_message, add_breadcrumb, set_user, set_tag, set_context
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


SENTRY_AVAILABLE = True

_SENTRY_INITIALIZED: bool = False
_LOGGER = None


def init_sentry() -> None:
    """Initialize Sentry once if DSN is provided via environment.

    Environment variables used:
      - SENTRY_DSN: DSN for Sentry project (required to enable)
      - SENTRY_ENVIRONMENT: environment name (default: development)
      - SENTRY_RELEASE: application release/version (optional)
      - SENTRY_TRACES_SAMPLE_RATE: float for performance tracing (default: 0.0)
      - SENTRY_PROFILES_SAMPLE_RATE: float for profiling (default: 0.0)
    """
    global _SENTRY_INITIALIZED, _LOGGER

    if _SENTRY_INITIALIZED:
        return

    if not SENTRY_AVAILABLE:
        _SENTRY_INITIALIZED = True
        return

    dsn: Optional[str] = os.getenv("SENTRY_DSN")
    if not dsn:
        _SENTRY_INITIALIZED = True
        return

    environment: str = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    release: Optional[str] = os.getenv("SENTRY_RELEASE")

    try:
        traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    except ValueError:
        traces_sample_rate = 0.1

    try:
        profiles_sample_rate: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))
    except ValueError:
        profiles_sample_rate = 0.0

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,      # Capture INFO and above as breadcrumbs
        event_level=logging.ERROR  # Send ERROR and above as events
    )

    # Configure integrations
    integrations = [logging_integration]
    
    if SqlalchemyIntegration:
        try:
            integrations.append(SqlalchemyIntegration())
        except Exception as e:
            print(f"Error initializing SqlalchemyIntegration: {e}")
            
    

    sentry_init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=False,
        integrations=integrations,
        before_send=_before_send_filter,
    )

    # Configure application logger
    _LOGGER = logging.getLogger("epic_events")
    _LOGGER.setLevel(logging.INFO)
    
    # Add console handler if not already present
    if not _LOGGER.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        _LOGGER.addHandler(console_handler)

    _SENTRY_INITIALIZED = True


def _before_send_filter(event, hint):
    """Filter events before sending to Sentry to remove sensitive information."""
    # Remove sensitive data from event
    event_to_send = {}
    sensitive_keys = ["password", "token", "secret", "key", "dsn"]
    for key in list(event.__dict__().keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_to_send[key] = "********"
        else:
            event_to_send[key] = event.__dict__()[key]
    
    return event_to_send


def get_logger():
    """Get the application logger."""
    if not _LOGGER:
        init_sentry()
    return _LOGGER or logging.getLogger("epic_events")


def log_error(error: Exception, context: Dict[str, Any] = None, user_id: int = None, level: str = "error") -> None:
    """Log an error with context to both Sentry and application logger."""
    logger = get_logger()
    
    # Set user context if provided
    if user_id and SENTRY_AVAILABLE:
        set_user({"id": user_id})
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("operation", context)
    
    # Log to application logger
    log_message = f"Error: {type(error).__name__}: {str(error)}"
    if context:
        log_message += f" | Context: {context}"
    
    if level == "error":
        logger.error(log_message)
    elif level == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    # Send to Sentry
    if SENTRY_AVAILABLE:
        capture_exception(error)


def log_info(message: str, context: Dict[str, Any] = None, user_id: int = None) -> None:
    """Log an info message with context."""
    logger = get_logger()
    
    # Set user context if provided
    if user_id and SENTRY_AVAILABLE:
        set_user({"id": user_id})
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("operation", context)
    
    # Log to application logger
    log_message = f"Info: {message}"
    if context:
        log_message += f" | Context: {context}"
    
    logger.info(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=message,
            level="info",
            data=context or {}
        )


def log_warning(message: str, context: Dict[str, Any] = None, user_id: int = None) -> None:
    """Log a warning message with context."""
    logger = get_logger()
    
    # Set user context if provided
    if user_id and SENTRY_AVAILABLE:
        set_user({"id": user_id})
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("operation", context)
    
    # Log to application logger
    log_message = f"Warning: {message}"
    if context:
        log_message += f" | Context: {context}"
    
    logger.warning(log_message)
    
    # Send to Sentry
    if SENTRY_AVAILABLE:
        capture_message(message, level="warning")


def log_operation(operation: str, success: bool = True, context: Dict[str, Any] = None, user_id: int = None) -> None:
    """Log a business operation with success/failure status."""
    logger = get_logger()
    
    # Set user context if provided
    if user_id and SENTRY_AVAILABLE:
        set_user({"id": user_id})
    
    # Set operation tag
    if SENTRY_AVAILABLE:
        set_tag("operation", operation)
        set_tag("success", str(success))
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("operation_details", context)
    
    # Log to application logger
    status = "SUCCESS" if success else "FAILED"
    log_message = f"Operation: {operation} - {status}"
    if context:
        log_message += f" | Context: {context}"
    
    if success:
        logger.info(log_message)
    else:
        logger.error(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=f"{operation} - {status}",
            level="info" if success else "error",
            data=context or {}
        )


def log_authentication_event(event_type: str, username: str = None, success: bool = True, context: Dict[str, Any] = None) -> None:
    """Log authentication-related events."""
    logger = get_logger()
    
    # Set authentication context
    if SENTRY_AVAILABLE:
        set_tag("auth_event", event_type)
        set_tag("auth_success", str(success))
        if username:
            set_user({"username": username})
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("auth_details", context)
    
    # Log to application logger
    status = "SUCCESS" if success else "FAILED"
    log_message = f"Auth Event: {event_type} - {status}"
    if username:
        log_message += f" | User: {username}"
    if context:
        log_message += f" | Context: {context}"
    
    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=f"{event_type} - {status}",
            level="info" if success else "warning",
            data=context or {}
        )


def log_database_operation(operation: str, table: str, record_id: int = None, success: bool = True, context: Dict[str, Any] = None) -> None:
    """Log database operations."""
    logger = get_logger()
    
    # Set database context
    if SENTRY_AVAILABLE:
        set_tag("db_operation", operation)
        set_tag("db_table", table)
        set_tag("db_success", str(success))
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("db_details", context)
    
    # Log to application logger
    status = "SUCCESS" if success else "FAILED"
    log_message = f"DB Operation: {operation} on {table} - {status}"
    if record_id:
        log_message += f" | Record ID: {record_id}"
    if context:
        log_message += f" | Context: {context}"
    
    if success:
        logger.info(log_message)
    else:
        logger.error(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=f"{operation} on {table} - {status}",
            level="info" if success else "error",
            data=context or {}
        )


def log_permission_check(operation: str, user_role: str, required_role: str, granted: bool, context: Dict[str, Any] = None) -> None:
    """Log permission checks and access control events."""
    logger = get_logger()
    
    # Set permission context
    if SENTRY_AVAILABLE:
        set_tag("permission_check", operation)
        set_tag("user_role", user_role)
        set_tag("required_role", required_role)
        set_tag("permission_granted", str(granted))
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("permission_details", context)
    
    # Log to application logger
    status = "GRANTED" if granted else "DENIED"
    log_message = f"Permission: {operation} - {status} | User: {user_role} | Required: {required_role}"
    if context:
        log_message += f" | Context: {context}"
    
    if granted:
        logger.info(log_message)
    else:
        logger.warning(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=f"{operation} - {status}",
            level="info" if granted else "warning",
            data=context or {}
        )


def log_cli_command(
    command: str, 
    args: Dict[str, Any] = None, 
    success: bool = True, 
    context: Dict[str, 
    Any] = None) -> None:
    """Log CLI command execution."""
    logger = get_logger()
    
    # Set CLI context
    if SENTRY_AVAILABLE:
        set_tag("cli_command", command)
        set_tag("cli_success", str(success))
    
    # Set additional context
    if context and SENTRY_AVAILABLE:
        set_context("cli_details", context)
    
    # Log to application logger
    status = "SUCCESS" if success else "FAILED"
    log_message = f"CLI Command: {command} - {status}"
    if args:
        log_message += f" | Args: {args}"
    if context:
        log_message += f" | Context: {context}"
    
    if success:
        logger.info(log_message)
    else:
        logger.error(log_message)
    
    # Add breadcrumb to Sentry
    if SENTRY_AVAILABLE:
        add_breadcrumb(
            message=f"{command} - {status}",
            level="info" if success else "error",
            data=context or {}
        )


def log_exception_handler(func):
    """Decorator to automatically log exceptions in functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract context from function arguments
            context = {
                "function": func.__name__,
                "args": str(args)[:200],  # Limit length
                "kwargs": str(kwargs)[:200]  # Limit length
            }
            log_error(e, context=context)
            raise
    return wrapper


