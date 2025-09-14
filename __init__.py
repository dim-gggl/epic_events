def init_sentry() -> None:
    # Lazy import to avoid hard dependency at import time
    from src.sentry.observability import init_sentry as _init
    return _init()


def cli() -> None:
    # Lazy import to avoid hard dependency at import time
    from src.cli.main import cli as _cli
    return _cli()


def main() -> None:
    """Main entry point for Epic Events CRM application."""
    init_sentry()
    cli()


__all__ = ["cli", "init_sentry", "main"]

