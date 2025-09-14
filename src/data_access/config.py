import os, urllib.parse
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)

load_dotenv()

def _build_url():
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    # Check for required environment variables
    password = os.getenv("POSTGRES_PASSWORD")
    if password is None:
        raise ValueError(
            "POSTGRES_PASSWORD environment variable is required. "
            "Please create a .env file with your database configuration. "
            "See .env.example for reference."
        )
    
    # Percent-encode credentials to avoid DSN parsing issues
    pwd = urllib.parse.quote_plus(password)
    user = os.getenv("POSTGRES_USER", "epic_events_app")
    user_enc = urllib.parse.quote_plus(user)
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    database = os.getenv("POSTGRES_DB", "epic_events_db")
    database_enc = urllib.parse.quote_plus(database)
    port = os.getenv("POSTGRES_PORT", "5432")
    # Note: host and port are not URL-encoded; they must remain literal
    return f"postgresql+psycopg2://{user_enc}:{pwd}@{host}:{port}/{database_enc}"

metadata = MetaData(schema="epic_events")

class Base(DeclarativeBase):
    metadata = metadata

engine = create_engine(_build_url(), echo=False, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
