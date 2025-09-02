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
    pwd = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
    user = os.getenv("POSTGRES_USER", "")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    database = os.getenv("POSTGRES_DB", "")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{database}"

metadata = MetaData(schema="epic_events")

class Base(DeclarativeBase):
    metadata = metadata

engine = create_engine(_build_url(), echo=False, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
