import os, urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

pwd = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
user = os.getenv("POSTGRES_USER")
host = os.getenv("POSTGRES_HOST")
database = os.getenv("POSTGRES_DB")
port = os.getenv("POSTGRES_PORT")

url = f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{database}"
engine = create_engine(url, pool_pre_ping=True)

Session = sessionmaker(bind=engine)
Base = declarative_base()

