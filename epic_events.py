import os
import shutil

from dotenv import load_dotenv

if not os.path.exists(".env"):
    shutil.copy(".env.example", ".env")

from src.cli.main import cli
from src.sentry.observability import init_sentry

load_dotenv()

def main():
    """Main entry point for Epic Events CRM application."""
    init_sentry()
    cli()


if __name__ == "__main__":
    main()
