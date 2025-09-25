from collections.abc import Callable
from functools import wraps

from src.auth.hashing import hash_password
from src.auth.jwt.token_storage import get_user_info_from_token
from src.auth.permissions import login_required, require_permission
from src.crm.controllers.auth_controller import AuthController
from src.crm.controllers.controllers import (
    client_controller,
    company_controller,
    contract_controller,
    event_controller,
    user_controller,
)
from src.crm.controllers.services import DataService
from src.crm.views.views import view

auth_controller = AuthController()


def handle_permission_errors(func):
    """Decorator to handle PermissionError exceptions and display them via view."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except PermissionError as e:
            self.view.error_message(str(e))
            return
    return wrapper

class MainController:
    def __init__(self):
        self.auth_c = auth_controller
        self.user_c = user_controller
        self.client_c = client_controller
        self.contract_c = contract_controller
        self.event_c = event_controller
        self.company_c = company_controller
        self.view = view

    def ask(self, attrib: str):
        """Helper method to prompt user for input during manager creation."""
        return self.view.get_input(
            f"Entrez la valeur pour '{attrib}': "
        ).strip()

    def _check_on_value_and_normalize(self, value: str|None,
                                      view_func: Callable[[str], str],
                                      service_func: Callable[[str], str]):
        if not value:
            value = view_func(value)
        if value:
            normalized = service_func(value)
        if normalized:
            value = normalized
        else:
            self.view.wrong_message(f"Invalid {value}")
            return


    @handle_permission_errors
    @login_required
    @require_permission("user:create")
    def register_user(
        self,
        username: str | None = None,
        full_name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        role_id: int | None = None,
    ):
        """Register a new user using the service layer for validation."""
        service = DataService(self.view)

        # Collect and validate data through the service layer
        username = self._check_on_value_and_normalize(username,
                                                      self.view.get_username,
                                                      service.normalized_username)
        if not username:
            self.view.error_message("Invalid username")
            return

        full_name = self._check_on_value_and_normalize(full_name,
                                                      self.view.get_full_name,
                                                      service.normalized_free_text)
        if not full_name:
            self.view.error_message("Invalid full name")
            return

        email = self._check_on_value_and_normalize(email,
                                                  self.view.get_email,
                                                  service.normalized_email)
        if not email:
            self.view.error_message("Invalid email")
            return

        if not password:
            password = self.view.get_password_with_confirmation()

        if not role_id:
            role_id = self.view.get_role_id()

        # Convert position-based role_id to actual database ID
        role_id = service.normalized_role_id(role_id)
        if role_id:
            # If user provided 1, 2, or 3, convert to actual DB ID
            if role_id in [1, 2, 3]:
                actual_role_id = service.get_role_id_by_position(role_id)
                if not actual_role_id:
                    self.view.wrong_message("Role not found in database")
                    return
                role_id = actual_role_id
        else:
            self.view.wrong_message("Invalid role ID")
            return

        # Prepare data for manager - password will be hashed by UserManager
        user_data = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "password": password,  # Will be hashed by UserManager
            "role_id": role_id
        }

        try:
            user = self.user_c.manager.create(user_data)
            self.view.success_message(f"User {username} created successfully.")
            return user
        except Exception as e:
            self.view.error_message(f"Error while creating user: {e}")
            return

    @handle_permission_errors
    @login_required
    @require_permission("user:create")
    def create_user(
        self,
        username: str | None = None,
        full_name: str | None = None,
        email: str | None = None,
        role_id: int | None = None,
    ):
        """Create a user from provided CLI params without interactive prompts."""
        data = {}
        if username:
            data["username"] = username
        else:
            data["username"] = self.view.get_username()
        if full_name:
            data["full_name"] = full_name
        else:
            data["full_name"] = self.view.get_full_name()
        if email:
            data["email"] = email
        else:
            data["email"] = self.view.get_email()
        if role_id:
            data["role_id"] = role_id
        else:
            data["role_id"] = self.view.get_role_id()
        data["password_hash"] = hash_password(self.view.get_password())
        try:
            user = self.user_c.manager.create(data)
            self.view.display_user(user)
            return user
        except Exception as e:
            self.view.error_message(f"Error while creating user: {e}")
            return

    @handle_permission_errors
    @login_required
    @require_permission("user:update")
    def update_user(self, **kwargs):
        self.user_c.update(**kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("user:list")
    def list_users(self, management=False, commercial=False, support=False):
        # For now, just call the basic list method
        # TODO: Implement role-based filtering if needed
        self.user_c.get_list()

    @handle_permission_errors
    @login_required
    @require_permission("user:view")
    def view_user(self, user_id: int):
        self.user_c.view(user_id)

    @handle_permission_errors
    @login_required
    @require_permission("user:delete")
    def delete_user(self, user_id: int):
        self.user_c.delete(user_id)

    @handle_permission_errors
    @login_required
    @require_permission("client:create")
    def create_client(self, **kwargs):
        # Seuls les commerciaux peuvent créer des clients
        self.client_c.create(**kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("client:update")
    def update_client(self, client_id: int, **kwargs):
        # Seuls les commerciaux peuvent modifier leurs clients
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to update a client.")
            return
        return self.client_c.manager.update(client_id, kwargs, user_info)

    @handle_permission_errors
    @login_required
    @require_permission("client:list")
    def list_clients(self, only_mine: bool = False):
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to list clients.")
            return

        # Use EntityController's get_list but pass the special parameters needed for ClientManager
        clients = self.client_c.manager.list(user_info['user_id'], filtered=only_mine)
        if not clients:
            self.view.wrong_message("No clients found.")
            return

        # Display the clients as a list
        self.view.display_clients(clients)

    @handle_permission_errors
    @login_required
    @require_permission("client:view")
    def view_client(self, client_id: int):
        self.client_c.view(client_id)

    @handle_permission_errors
    @login_required
    @require_permission("client:delete")
    def delete_client(self, client_id: int):
        # Seuls les commerciaux peuvent supprimer leurs clients
        self.client_c.delete(client_id)

    @handle_permission_errors
    @login_required
    @require_permission("contract:create")
    def create_contract(self, **kwargs):
        # Commerciaux: création libre, Managers: seulement si client-commercial déjà liés
        self.contract_c.create(**kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("contract:update")
    def update_contract(self, contract_id: int, **kwargs):
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to update a contract.")
            return
        return self.contract_c.manager.update(contract_id, kwargs, user_info['user_id'])

    @handle_permission_errors
    @login_required
    @require_permission("contract:list")
    def list_contracts(self,
                       only_mine: bool = False,
                       unsigned: bool = False,
                       unpaid: bool = False):
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to list contracts.")
            return

        contracts = self.contract_c.manager.list(user_info['user_id'],
                                                filtered=only_mine,
                                                unsigned=unsigned,
                                                unpaid=unpaid)
        if not contracts:
            self.view.wrong_message("No contracts found.")
            return

        fields = self.contract_c.fields or self.contract_c._get_list_fields()
        for contract in contracts:
            self.view.display_details(contract, fields)

    @handle_permission_errors
    @login_required
    @require_permission("contract:view")
    def view_contract(self, contract_id: int):
        self.contract_c.view(contract_id)

    @handle_permission_errors
    @login_required
    @require_permission("contract:delete")
    def delete_contract(self, contract_id: int):
        self.contract_c.delete(contract_id)

    @handle_permission_errors
    @login_required
    @require_permission("event:create")
    def create_event(self, **kwargs):
        # Commerciaux: pour leurs clients, Managers: seulement si contrat signé
        self.event_c.create(**kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("event:update")
    def update_event(self, event_id: int, **kwargs):
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to update an event.")
            return
        return self.event_c.manager.update(event_id, kwargs, user_info)

    @handle_permission_errors
    @login_required
    @require_permission("event:list")
    def list_events(self, only_mine: bool = False, unassigned_only: bool = False):
        user_info = get_user_info_from_token()
        if not user_info:
            self.view.error_message("You must be logged in to list events.")
            return

        events = self.event_c.manager.list(user_info['user_id'],
                                           filtered=only_mine,
                                           unassigned_only=unassigned_only)
        if not events:
            self.view.wrong_message("No events found.")
            return

        fields = self.event_c.fields or self.event_c._get_list_fields()
        for event in events:
            self.view.display_details(event, fields)

    @handle_permission_errors
    @login_required
    @require_permission("event:view")
    def view_event(self, event_id: int):
        self.event_c.view(event_id)

    @handle_permission_errors
    @login_required
    @require_permission("event:delete")
    def delete_event(self, event_id: int):
        self.event_c.delete(event_id)

    @handle_permission_errors
    @login_required
    @require_permission("event:update")
    def assign_support_to_event(self, event_id: int, support_id: int):
        return self.event_c.manager.assign_support(event_id, support_id)

    @handle_permission_errors
    @login_required
    @require_permission("company:create")
    def create_company(self, **kwargs):
        self.company_c.create(**kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("company:update")
    def update_company(self, company_id: int, **kwargs):
        self.company_c.update(company_id, **kwargs)

    @handle_permission_errors
    @login_required
    @require_permission("company:list")
    def list_companies(self):
        companies = self.company_c.manager.list()
        if not companies:
            self.view.wrong_message("No companies found.")
            return

        fields = self.company_c.fields or self.company_c._get_list_fields()
        for company in companies:
            self.view.display_details(company, fields)

    @handle_permission_errors
    @login_required
    @require_permission("company:view")
    def view_company(self, company_id: int):
        self.company_c.view(company_id)

    @handle_permission_errors
    @login_required
    @require_permission("company:delete")
    def delete_company(self, company_id: int):
        self.company_c.delete(company_id)

    def login(self, username: str, password: str):
        self.auth_c.login(username, password)

    def refresh(self):
        self.auth_c.refresh()

    def logout(self):
        self.auth_c.logout()

    def db_create(self):
        self.auth_c.db_create()

    def manager_create(self, args: dict = None):
        """
        Create the first manager user when no users exist yet.
        This is a bootstrap function for initial system setup.

        Args:
            args: Optional dictionary with user data
        """
        if args is None:
            args = {}

        # Collect required user data
        required_fields = {
            "username": args.get("username", None),
            "password": args.get("password", None),
            "full_name": args.get("full_name", None),
            "email": args.get("email", None)
        }

        # Prompt for missing fields
        for field, value in required_fields.items():
            if not value:
                required_fields[field] = self.ask(field)

        # Create the manager user through auth controller
        self.auth_c.manager_create(**required_fields)


# Global instance
main_controller = MainController()
