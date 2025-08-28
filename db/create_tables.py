'''
Tutorial link: https://docs.sqlalchemy.org/en/latest/orm/tutorial.html
Sqlalchemy version: 1.2.15
Python version: 3.7
'''

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.config import Base, engine, Session
from crm.models import Role, User, Client, Company, Contract, Event, Venue


def start():
    session = Session()
    Base.metadata.create_all(engine)
    return engine, session

def init_db():
    engine, session = start()

    User.__table__.create(engine)
    Client.__table__.create(engine)
    Company.__table__.create(engine)
    Contract.__table__.create(engine)
    Event.__table__.create(engine)
    Venue.__table__.create(engine)
