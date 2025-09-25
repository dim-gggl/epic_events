from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.decorators import login_required
from src.data_access.config import Session
from src.exceptions import InvalidIdError


class EntityManager:
    """
    A base class for object persistence operations.
    It provides CRUD operations for a given Python entity where
    the entity is basically a Python class.

    Attributes:
        entity: The Python class to be managed.
        name: The name of the entity.

    Methods:
        create: Create a new instance of the entity.
        list: List all instances of the entity.
        view: View an instance of the entity.
        update: Update an instance of the entity.
        delete: Delete an instance of the entity.
    """
    def __init__(self, entity: Any):
        self.entity = entity
        self.name = entity.__name__.lower()

    def create(self, data: dict):
        with Session() as session:
            new_instance = self.entity(**data)
            session.add(new_instance)
            session.commit()
            session.refresh(new_instance)
            return new_instance

    @login_required
    def list(self):
        with Session() as session:
            return session.scalars(select(self.entity)).all()

    def view(self, id: int, session: Session = None):
        """
        View an instance of the entity by its id.

        Argument:
            - id: int. Required. The id of the wanted instance.
            - session: Optional existing session to use.

        Returns:
            The entity instance or None if not found.
        """
        if session:
            return session.scalars(
                select(self.entity).filter(self.entity.id == id)
            ).first()
        else:
            with Session() as new_session:
                return new_session.scalars(
                    select(self.entity).filter(self.entity.id == id)
                ).first()

    def get_by_id(self, id: int, session: Session = None):
        """
        Get an instance of the entity by its id.

        Argument:
            - id: int. Required. The id of the wanted instance.
            - session: Optional existing session to use.

        Raises:
            - InvalidIdError if the entity is not found.
        """
        entity = self.view(id, session)
        if not entity:
            raise InvalidIdError(
                f"{self.entity.__name__} with id {id} not found"
            )
        return entity

    def update(self, id: int, data: dict):
        """
        Update an instance of the entity by its id.

        Parameters:
            id: The id of the entity to update.
            data: A dict of the fields to update.

        Returns:
            The updated entity.
            None if the entity is not found.
        """
        with Session() as session:
            try:
                entity = self.get_by_id(id, session)
                for key, value in data.items():
                    setattr(entity, key, value)
                session.add(entity)
                session.commit()
                session.refresh(entity)
                return entity
            except InvalidIdError as e:
                print(e)
                return

    def delete(self, id: int) -> bool:
        """
        Delete the instance from the database and commit

        Argument:
            - id: int. Required. The id of the instance
            supposed to get deleted.

        Returns:
            - bool.
            Usage : is_deleted = manager.delete(instance_)
        """
        with Session() as session:
            try:
                entity = self.get_by_id(id, session)
                session.delete(entity)
                session.commit()
                return True
            except InvalidIdError:
                raise InvalidIdError(
                    "Incorrect ID.\nImpossible to delete instance of Nonetype"
                )
