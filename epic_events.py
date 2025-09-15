
from src.cli.main import cli
from src.sentry.observability import init_sentry


def main():
    """Main entry point for Epic Events CRM application."""
    init_sentry()
    cli()


if __name__ == "__main__":
    main()
