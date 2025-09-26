from abc import ABC, abstractmethod

from sqlalchemy import inspect

from src.auth.decorators import in_session
from src.auth.jwt.token_storage import get_user_info_from_token
from src.auth.permissions import login_required
from src.auth.validators import is_valid_email, is_valid_username
from src.crm.controllers.managers import manager_repertory
from src.crm.controllers.services import DataService
from src.crm.models import Client, Company, Contract, Event, User
from src.crm.views.helper_view import HelperView
from src.crm.views.views import view
from src.data_access.config import Session

get_manager_for = manager_repertory.get

session = Session()
helper_view = HelperView()



class Controller(ABC):
	@abstractmethod
	def create(self, *args, **kwargs):
		pass

	@abstractmethod
	def get_list(self, *args, **kwargs):
		pass

	@abstractmethod
	def view(self, *args, **kwargs):
		pass

	@abstractmethod
	def update(self, *args, **kwargs):
		pass

	@abstractmethod
	def delete(self, *args, **kwargs):
		pass

class EntityController(Controller):
    """
    A base controller class to manipulate a specific instance of
    any of the CRM classes.
    Makes the bridge between manager and view in order to proceed to any
    CRUD operation.

    params:
        - entity: class [User | Client | Contract | Event | Company]
        	Represents the class of the objects this controller is organizing.
        - fields: list[str]
        	Represents the list of attributes that must be displayed when we call
        	for list or view on self.entity.
        - entity_name: str.
        	A lower-case string version of the name of the class of self.entity
        - manager: EntityManager
        	Represents an instance of manager pointing towards the same model
        	that will handle the moves from the business logic side.
        
    """
    def __init__(self, entity: type, fields: list[str] | None=None):
        self.entity = entity
        self.fields = fields
        if not self.fields:
            self.fields = self._get_required_fields()
        self.entity_name = entity.__name__.lower()
        self.manager = get_manager_for(self.entity_name)
        self.required_fields = self._get_required_fields()

    def _get_required_fields(self):
        """
        Gets the list of required fields for an entity by inspecting the model.
        Returns fields that are nullable=False, excluding auto-generated fields.
        """
        mapper = inspect(self.entity)
        required_fields = []

        for column in mapper.columns:
            # Skip auto-generated fields (primary keys with autoincrement,
			# timestamps with server_default)
            # But include user-input fields that are nullable=False
            if (column.nullable is False
			and not (column.primary_key and column.autoincrement)
			and not column.server_default
			and column.name not in ['id',
									'created_at',
									'updated_at',
									'commercial_id']):
                required_fields.append(column.name)
        return required_fields

    def _validate_entity_data(self, service: DataService, data: dict) -> dict | None:
        """
        Validate entity data using appropriate DataService validator.
        Returns validated data or None if validation fails.
        """
        match self.entity_name:
            case "user":
                return service.validate_and_normalize_user_data(data)
            case "client":
                return service.validate_and_normalize_client_data(data)
            case "company":
                return service.validate_and_normalize_company_data(data)
            case "contract":
                return service.validate_and_normalize_contract_data(data)
            case "event":
                return service.validate_and_normalize_event_data(data)
            case _:
                # For entities without specialized validation, return as-is
                return data

    def _validate_entity_data_for_update(self, service: DataService, data: dict, entity_id: int) -> dict | None:
        """
        Validate entity data for updates using appropriate DataService validator.
        Excludes current entity ID from uniqueness checks.
        Returns validated data or None if validation fails.
        """
        match self.entity_name:
            case "user":
                return service.validate_and_normalize_user_data(data, exclude_user_id=entity_id)
            case "client":
                return service.validate_and_normalize_client_data(data, exclude_client_id=entity_id)
            case "company":
                return service.validate_and_normalize_company_data(data)
            case "contract":
                return service.validate_and_normalize_contract_data(data)
            case "event":
                return service.validate_and_normalize_event_data(data)
            case _:
                # For entities without specialized validation, return as-is
                return data

    @in_session(session)
    def create(self, *args, **kwargs):
        """
        Create a new entity instance using required fields.
        Args can be used to provide positional values for
        required fields,
        kwargs for named values. If a required field is
        missing, prompt the user.
        """
        data = {k: v for k, v in kwargs.items()}

        for i, arg in enumerate(args):
            if i < len(self.required_fields):
                field_name = self.required_fields[i]
                if field_name not in data:
                    data[field_name] = arg
            else:
                view.error_message(
                    f"Argument '{arg}' does not match "
					f"any field in {self.entity_name}."
                )

        # Prompt user for any missing required fields
        for field in self.required_fields:
            if field not in data or not data[field]:
                prompt = f"{field.replace('_', ' ').title()} : "
                user_input = view.get_input(prompt).strip()
                data[field] = user_input

        # Special handling for optional fields - only if not provided via CLI
        if (self.entity_name == "client" and
            'phone' not in data and
            kwargs.get('phone') is None):
            phone = view.get_input(
                "Enter client phone number (optional, press Enter to skip): "
            ).strip()
            if phone:
                data['phone'] = phone

        # Validate and normalize data using DataService
        service = DataService(view)
        validated_data = self._validate_entity_data(service, data)
        if validated_data is None:
            return None  # Validation failed, error already displayed

        # Attempt to create the entity
        try:
            user_info = get_user_info_from_token()
            if not user_info:
                view.error_message("You must be logged in to create an entity.")
                return

            # Special cases for managers that require additional parameters
            if self.entity_name == "client":
                new_obj = self.manager.create(validated_data, user_info['user_id'])
            elif self.entity_name == "event":
                new_obj = self.manager.create(validated_data, user_info)
            else:
                new_obj = self.manager.create(validated_data)
            view.success_message(f"{self.entity_name} created successfully.")
            return new_obj
        except Exception as e:
            view.error_message(
                f"Error while creating {self.entity_name}: {e}"
            )
            return

    @in_session(session)
    @login_required
    def get_list(self, fields: list[str]=None, **kwargs):
        if not fields:
            fields = self._get_required_fields()
        if not fields:
            fields = self.fields

        elements = self.manager.list(**kwargs)
        if not elements:
            view.wrong_message(f"No {self.entity_name}s found.")
            return
        view.display_list(elements, fields)

    @in_session(session)
    def view(self, id: int, fields: list[str]=None):
        obj = self.manager.get_instance(id)
        if obj:
            view.display_details(obj, fields or self.fields)
        else:
            view.wrong_message(f"{self.entity_name} with id {id} not found.")

    @in_session(session)
    def update(self, id: int, *args, fields: list[str]=None, **kwargs):
        entity = self.manager.get_instance(id)
        if not entity:
            view.error_message(f"{self.entity_name} with id {id} not found.")
            return None

        # Validate and normalize update data using DataService
        service = DataService(view)
        validated_data = self._validate_entity_data_for_update(service, kwargs, id)
        if validated_data is None:
            return None  # Validation failed, error already displayed

        fields = fields or self.fields
        for k, v in validated_data.items():
            if k in fields and v is not None:
                setattr(entity, k, v)
        session.add(entity)
        session.commit()
        view.success_message(f"{self.entity_name} updated successfully.")
        view.display_details(entity, fields or self.fields)
        return entity

    @in_session(session)
    def delete(self, id:int, fields: list[str]=None) -> bool:

        entity = self.manager.get_instance(id)
        if not entity:
            view.wrong_message(
                f"{self.entity_name} with id {id} not found."
            )
            return False

        # Special validation for client deletion by managers
        if self.entity_name == "client":
            user_info = get_user_info_from_token()
            if user_info and user_info['role_id'] == 1:  # Management
                view.error_message(
                    "Managers cannot delete clients. "
                    "Only commercial users can delete their clients."
                )
                return False

        sure = view.sure_to_delete(entity).strip().lower()
        if sure in ["yes", "y"]:
            session = Session()
            session.delete(entity)
            session.commit()
            view.success_message(f"{self.entity_name} deleted successfully.")
            return True
        else:
            view.wrong_message(f"{self.entity_name} not found")
            return False


class ClientController(EntityController):
    def __init__(self):
        super().__init__(Client,
                         ["id",
                         "full_name",
                         "email",
                         "phone",
                         "company_id",
                         "first_contact_date",
                         "last_contact_date"])

    def create(self, *args, **kwargs):
        """
        Create a new client - phone field is handled as optional in parent method.
        """
        
        return super().create(*args, **kwargs)


class UserController(EntityController):
    def __init__(self):
        self.service = DataService()
        super().__init__(User,
                         ["id",
                         "username",
                         "full_name",
                         "email",
                         "role_id"])

    def get_username(self, username: str | None=None):
        is_valid = False
        while not is_valid:
            username = view.get_username().strip()
            if not is_valid_username(username):
                continue
            else:
                is_valid = True
        normalized = self.service.normalized_username(
            username
        )
        if normalized:
            username = normalized
        return username

    def get_full_name(self, full_name: str | None=None):
        if not full_name:
            while not full_name:
                full_name = view.get_full_name().strip()
        normalized = self.service.normalized_free_text(full_name)
        if normalized:
            full_name = normalized
        return full_name

    def get_email(self, email: str | None=None):
        if not email:
            email = view.get_email().strip()
            while not is_valid_email(email):
                helper_view.email_helper()
                email = view.get_email().strip()
        normalized = self.service.normalized_email(email)
        if normalized:
            email = normalized
        return email

    def get_list(self, management=False, commercial=False, support=False):
        super().get_list(
            ["id", "username", "role_id"],
            management=management,
            commercial=commercial,
            support=support
        )


# Controller instances
user_controller = UserController()
client_controller = ClientController()

contract_controller = EntityController(Contract,
                                      ["id",
                                      "client_id",
                                      "commercial_id",
                                      "total_amount",
                                      "remaining_amount",
                                      "is_signed",
                                      "is_fully_paid"])

event_controller = EntityController(Event,
                                      ["id",
                                      "contract_id",
                                      "title",
                                      "full_address",
                                      "support_contact_id",
                                      "start_date",
                                      "end_date",
                                      "participant_count",
                                      "notes"])

company_controller = EntityController(Company,
                                      ["id",
                                      "name"])
