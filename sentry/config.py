import sentry_sdk, logging, os

from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration


load_dotenv()


SENTRY_DSN = os.getenv("SENTRY_DSN")
if not SENTRY_DSN:
    print("SENTRY_DSN is not set")
    

sentry_sdk.init(
    dsn=SENTRY_DSN,
    max_breadcrumbs=50,
    traces_sampler=8.0,
    enable_logs=True,
    debug=True,
    environment=os.getenv("SENTRY_ENVIRONMENT"),
    integrations=[
        # Only send WARNING (and higher) logs to Sentry logs,
        # even if the logger is set to a lower level.
        LoggingIntegration(sentry_logs_level=logging.WARNING),
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)