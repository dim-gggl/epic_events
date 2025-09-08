import os
import logging

from typing import Optional

try:
    from sentry_sdk import init as sentry_init
    from sentry_sdk.integrations.logging import LoggingIntegration
    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  
    except Exception:  
        SqlalchemyIntegration = None
except Exception:
    sentry_init = None
    LoggingIntegration = None
    SqlalchemyIntegration = None


_SENTRY_INITIALIZED: bool = False


def init_sentry() -> None:
    """Initialize Sentry once if DSN is provided via environment.

    Environment variables used:
      - SENTRY_DSN: DSN for Sentry project (required to enable)
      - SENTRY_ENVIRONMENT: environment name (default: development)
      - SENTRY_RELEASE: application release/version (optional)
      - SENTRY_TRACES_SAMPLE_RATE: float for performance tracing (default: 0.0)
      - SENTRY_PROFILES_SAMPLE_RATE: float for profiling (default: 0.0)
    """
    global _SENTRY_INITIALIZED

    if _SENTRY_INITIALIZED:
        return

    if sentry_init is None:
        _SENTRY_INITIALIZED = True
        return

    dsn: Optional[str] = os.getenv("SENTRY_DSN")
    if not dsn:
        _SENTRY_INITIALIZED = True
        return

    environment: str = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    release: Optional[str] = os.getenv("SENTRY_RELEASE")

    try:
        traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
    except ValueError:
        traces_sample_rate = 0.0

    try:
        profiles_sample_rate: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))
    except ValueError:
        profiles_sample_rate = 0.0

    logging_integration = LoggingIntegration(
        level=logging.INFO,      # Capture INFO and above as breadcrumbs
        event_level=logging.ERROR  # Send ERROR and above as events
    )

    integrations = [logging_integration]
    if SqlalchemyIntegration is not None:
        try:
            integrations.append(SqlalchemyIntegration())
        except Exception:
            pass

    sentry_init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=False,
        integrations=integrations,
    )

    _SENTRY_INITIALIZED = True


