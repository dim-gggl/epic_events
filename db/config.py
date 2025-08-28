import os, urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{database}"

NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(schema="epic_events", naming_convention=NAMING)

class Base(DeclarativeBase):
    metadata = metadata

engine = create_engine(_build_url(), echo=True, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
