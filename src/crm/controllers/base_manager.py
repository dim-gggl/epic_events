from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import select

from src.auth.decorators import login_required, in_session
from src.data_access.config import Session
from src.exceptions import InvalidIdError

session = Session()


class Manager(ABC):
	@abstractmethod
	def create(self, data: dict):
		pass

	@abstractmethod
	def get_list(self):
		pass

	@abstractmethod
	def get_instance(self, id: int):
		pass

	@abstractmethod
	def update(self, id: int, data: dict):
		pass

	@abstractmethod
	def delete(self, id: int):
		pass


class EntityManager(Manager):
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

    @in_session(session)
    def create(self, data: dict):
        new_instance = self.entity(**data)
        session.add(new_instance)
        session.commit()
        session.refresh(new_instance)
        return new_instance

    @in_session(session=session)
    @login_required
    def get_list(self):
        return session.query(self.entity).all()

    @in_session(session=session)
    def get_instance(self, id: int):
        """
        View an instance of the entity by its id.

        Argument:
            - id: int. Required. The id of the wanted instance.
            - session: Optional existing session to use.

        Returns:
            The entity instance or None if not found.
        """
        return session.query(self.entity).filter(self.entity.id == id).first()

    @in_session(session=session)
    def view(self, id: int):
        """
        Get an entity instance and its fields for display.

        Argument:
            - id: int. Required. The id of the wanted instance.

        Returns:
            Tuple of (entity instance, list of field names) or (None, []) if not found.
        """
        entity = self.get_instance(id)
        if not entity:
            return None, []

        # Get all column names from the entity
        from sqlalchemy import inspect
        mapper = inspect(self.entity)
        fields = [column.name for column in mapper.columns]

        return entity, fields

    @in_session(session=session)
    def get_by_id(self, id: int):
        """
        Get an instance of the entity by its id.

        Argument:
            - id: int. Required. The id of the wanted instance.
            - session: Optional existing session to use.

        Raises:
            - InvalidIdError if the entity is not found.
        """
        entity = self.get_instance(id)
        if not entity:
            raise InvalidIdError(
                f"{self.entity.__name__} with id {id} not found"
            )
        return entity

    @in_session(session)
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
        try:
            entity = self.get_by_id(id)
            for key, value in data.items():
                setattr(entity, key, value)
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except InvalidIdError as e:
            print(e)
            return

    @in_session(session)
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
        try:
            entity = self.get_by_id(id)
            session.delete(entity)
            session.commit()
            return True
        except InvalidIdError:
            raise InvalidIdError(
                "Incorrect ID.\nImpossible to delete instance of Nonetype"
            )
