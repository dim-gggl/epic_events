'''
Tutorial link: https://docs.sqlalchemy.org/en/latest/orm/tutorial.html
Sqlalchemy version: 1.2.15
Python version: 3.7
'''
from db.config import engine, Session, metadata
from crm.models import Role, User, Client, Company, Contract, Event


def init_db():
    session = Session()
    metadata.create_all(engine)
    session.commit()
    session.close()
