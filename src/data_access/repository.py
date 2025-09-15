from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.crm.models import Base
from src.crm.models import (Client, 
                            Company, 
                            Contract, 
                            Event, 
                            Role, 
                            User)

T = TypeVar('T', bound=Base)

class Repository(Generic[T]):
    """
    A generic repository for CRUD operations on a SQLAlchemy model.
    """
    def __init__(self, model: type[T]):
        self.model = model

    def create(self, data: dict[str, Any], session: Session) -> T:
        """
        Create a new record in the database.
        """
        instance = self.model(**data)
        session.add(instance)
        return instance

    def get_by_id(self, id: int, session: Session) -> T | None:
        """
        Get a record by its ID.
        """
        return session.get(self.model, id)

    def get_all(self, session: Session) -> list[T]:
        """
        Get all records for the model.
        """
        return session.scalars(select(self.model)).all()

    def update(self, id: int, data: dict[str, Any], session: Session) -> T | None:
        """
        Update a record by its ID.
        """
        instance = self.get_by_id(id, session)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
        return instance

    def delete(self, id: int, session: Session) -> bool:
        """
        Delete a record by its ID.
        """
        instance = self.get_by_id(id, session)
        if instance:
            session.delete(instance)
            return True
        return False

    def find_by(self, session: Session, **kwargs) -> list[T]:
        """
        Find records by specific criteria.
        """
        return session.scalars(select(self.model).filter_by(**kwargs)).all()


class UserRepository(Repository[User]):
    def __init__(self):
        super().__init__(User)

class ClientRepository(Repository[Client]):
    def __init__(self):
        super().__init__(Client)

class ContractRepository(Repository[Contract]):
    def __init__(self):
        super().__init__(Contract)

class EventRepository(Repository[Event]):
    def __init__(self):
        super().__init__(Event)

class CompanyRepository(Repository[Company]):
    def __init__(self):
        super().__init__(Company)

class RoleRepository(Repository[Role]):
    def __init__(self):
        super().__init__(Role)

# Instantiate repositories
user_repository = UserRepository()
client_repository = ClientRepository()
contract_repository = ContractRepository()
event_repository = EventRepository()
company_repository = CompanyRepository()
role_repository = RoleRepository()
