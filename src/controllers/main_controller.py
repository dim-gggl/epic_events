from __future__ import annotations
from typing import Callable, Any, Optional
from datetime import datetime

from src.auth.validators import (
    is_valid_username, 
    is_valid_email, 
    is_valid_password, 
    is_valid_role_id, 
    is_valid_phone
)
from src.auth.permissions import has_permission
from src.auth.jwt.verify_token import verify_access_token
from src.views.views import MainView
from src.business_logic.client_logic import client_logic
from src.business_logic.contract_logic import contract_logic
from src.business_logic.event_logic import event_logic
from src.business_logic.user_logic import user_logic
from src.business_logic.company_logic import company_logic
from src.auth.jwt.token_storage import get_user_info
from src.auth.login import login as login_user
from src.auth.logout import logout as logout_user

view = MainView()

DATE_FMT = "%d/%m/%Y"

def _ask(
    prompt: Callable[[], str],
    *,
    cast: Callable[[str], Any] = lambda s: s,
    validate: Optional[Callable[[Any], bool]] = None,
    required_msg: str,
    invalid_msg: Optional[str] = None,
    strip: bool = True,
) -> Any:
    while True:
        raw = prompt()
        if strip:
            raw = raw.strip()
        if not raw:
            view.wrong_message(required_msg)
            continue
        try:
            value = cast(raw)
        except Exception:
            view.wrong_message(invalid_msg or required_msg)
            continue
        if validate is None or validate(value):
            return value
        view.wrong_message(invalid_msg or required_msg)

def _to_int(s: str) -> int:
    return int(s)

def _to_float(s: str) -> float:
    s_norm = s.replace(" ", "").replace(",", ".")
    return float(s_norm)

def _to_date(s: str) -> datetime:
    return datetime.strptime(s, DATE_FMT)

def _to_bool_yes_no(s: str) -> bool:
    s = s.strip().lower()
    if s in {"y", "Y", "yes", "Yes", "YES"}:
        return True
    if s in {"n", "N", "no", "No", "NO"}:
        return False
    raise ValueError("Expected yes/no")

def _ask_optional(
    prompt: Callable[[], str],
    *,
    cast: Callable[[str], Any] = lambda s: s,
    validate: Optional[Callable[[Any], bool]] = None,
    invalid_msg: Optional[str] = None,
    strip: bool = True,
) -> Any:
    while True:
        raw = prompt()
        if strip:
            raw = raw.strip()
        if not raw:
            return None
        try:
            value = cast(raw)
        except Exception:
            if invalid_msg:
                view.wrong_message(invalid_msg)
            continue
        if validate is None or validate(value):
            return value
        if invalid_msg:
            view.wrong_message(invalid_msg)

class MainController:

    # Authentication
    def login(self, username, password):
        login_user(username, password)

    def logout(self):
        logout_user()

    # User input gathering
    def get_user_data(self) -> dict:
        username = _ask(view.get_username, required_msg="Username is required.", validate=is_valid_username)
        full_name = _ask(view.get_full_name, required_msg="Full name is required.")
        email = _ask(view.get_email, required_msg="Email is required.", validate=is_valid_email)
        password = _ask(view._prompt_password, required_msg="Password is required.", validate=is_valid_password)
        role_id = _ask(view.get_role_id, cast=_to_int, required_msg="Role ID is required.", validate=is_valid_role_id)
        return {"username": username, "full_name": full_name, "email": email, "password": password, "role_id": role_id}

    def get_client_data(self) -> dict:
        full_name = _ask(lambda: view.get_full_name(), required_msg="Full name is required.")
        email = _ask(lambda: view.get_email(), required_msg="Email is required.", invalid_msg="Invalid email address.", validate=is_valid_email)
        phone = _ask(lambda: view.get_phone(), required_msg="Phone number is required.", invalid_msg="Invalid phone number. Please try again.", validate=is_valid_phone)
        company_id = _ask(lambda: view.get_company_id(), cast=_to_int, required_msg="Company ID is required.", invalid_msg="Company ID must be an integer.")
        first_contact_date = _ask(lambda: view.get_first_contact_date(), cast=_to_date, required_msg="The date of the first contact with the client.", invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.")
        last_contact_date = _ask(lambda: view.get_last_contact_date(), cast=_to_date, required_msg="The date of the last contact with the client.", invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.")
        return {"full_name": full_name, "email": email, "phone": phone, "company_id": company_id, "first_contact_date": first_contact_date, "last_contact_date": last_contact_date}

    def get_contract_data(self) -> dict:
        client_id = _ask(lambda: view.get_client_id(), cast=_to_int, required_msg="Client ID is required.")
        total_amount = _ask(lambda: view.get_total_amount(), cast=_to_float, required_msg="Total amount is required.")
        remaining_amount = _ask(lambda: view.get_remaining_amount(), cast=_to_float, required_msg="Remaining amount is required.")
        is_signed = _ask(lambda: view.get_is_signed(), cast=_to_bool_yes_no, required_msg="Is signed is required.")
        is_fully_paid = _ask(lambda: view.get_is_fully_paid(), cast=_to_bool_yes_no, required_msg="Is fully paid is required.")
        return {"client_id": client_id, "total_amount": total_amount, "remaining_amount": remaining_amount, "is_signed": is_signed, "is_fully_paid": is_fully_paid}
        
    def get_event_data(self) -> dict:
        contract_id = _ask(lambda: view.get_contract_id(), cast=_to_int, required_msg="Contract ID is required.")
        title = _ask(lambda: view.get_title(), required_msg="Title is required.")
        full_address = _ask(lambda: view.get_full_address(), required_msg="Full address is required.")
        support_contact_id = _ask(lambda: view.get_support_contact_id(), cast=_to_int, required_msg="Support contact ID is required.")
        start_date = _ask(lambda: view.get_start_date(), cast=_to_date, required_msg="Start date is required.", invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.")
        end_date = _ask(lambda: view.get_end_date(), cast=_to_date, required_msg="End date is required.", invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.")
        participant_count = _ask(lambda: view.get_participant_count(), cast=_to_int, required_msg="Participant count is required.")
        notes = _ask(lambda: view.get_notes(), required_msg="Notes are required.")
        return {"contract_id": contract_id, "title": title, "full_address": full_address, "support_contact_id": support_contact_id, "start_date": start_date, "end_date": end_date, "participant_count": participant_count, "notes": notes}

    def get_company_data(self) -> dict:
        name = _ask(view.get_company_name, required_msg="Company name is required.")
        return {"name": name}

    # CRUD methods
    # User
    def create_user(self, access_token: str):
        try:
            user_data = self.get_user_data()
            user = user_logic.create_user(user_data)
            view.success_message(f"User '{user.username}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_users(self, access_token: str):
        try:
            users = user_logic.get_users(access_token)
            view.display_users(users)
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
    
    def view_user(self, access_token: str, user_id: int):
        try:
            user = user_logic.get_user_by_id(user_id)
            if user:
                view.display_user(user)
            else:
                view.wrong_message("User not found.")
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_user(self, access_token: str, user_id: int):
        try:
            user_data = self.get_user_data()
            user = user_logic.update_user(access_token, user_id, user_data)
            if user:
                view.success_message(f"User '{user.username}' updated successfully.")
            else:
                view.wrong_message("User not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def delete_user(self, access_token: str, user_id_to_delete: int):
        try:
            user_info = get_user_info()
            current_user_id = user_info['user_id']
            if user_logic.delete_user(access_token, current_user_id, user_id_to_delete):
                view.success_message("User deleted successfully.")
            else:
                view.wrong_message("User not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    # Client
    def create_client(self, access_token: str):
        try:
            # Check if user has permission to create clients
            if not has_permission(access_token, "client:create"):
                raise PermissionError("You don't have permission to create clients.")
            
            user_info = get_user_info()
            user_id = user_info['user_id']
            client_data = self.get_client_data()
            client = client_logic.create_client(client_data, user_id)
            view.success_message(f"Client '{client.full_name}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_clients(self, access_token: str, filtered: bool):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            clients = client_logic.get_clients(access_token, user_id, filtered)
            view.display_list_clients(clients)
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
    
    def view_client(self, access_token: str, client_id: int):
        try:
            client = client_logic.get_client_by_id(client_id)
            if client:
                view.display_client_detail(access_token, client)
            else:
                view.wrong_message("Client not found.")
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_client(self, access_token: str, client_id: int):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            client_data = self.get_client_data()
            client = client_logic.update_client(access_token, user_id, client_id, client_data)
            if client:
                view.success_message(f"Client '{client.full_name}' updated successfully.")
            else:
                view.wrong_message("Client not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def delete_client(self, access_token: str, client_id: int):
        try:
            if client_logic.delete_client(access_token, client_id):
                view.success_message("Client deleted successfully.")
            else:
                view.wrong_message("Client not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    # Contract
    def create_contract(self, access_token: str):
        try:
            user_info = get_user_info()
            commercial_id = user_info['user_id']
            contract_data = self.get_contract_data()
            contract_data['commercial_id'] = commercial_id
            contract = contract_logic.create_contract(contract_data)
            view.success_message(f"Contract for client '{contract.client.full_name}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
    
    def list_contracts(self, access_token: str, filtered: bool):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            contracts = contract_logic.get_contracts(access_token, user_id, filtered)
            view.display_contracts(contracts)
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_contract(self, access_token: str, contract_id: int):
        try:
            contract = contract_logic.get_contract_by_id(contract_id)
            if contract:
                view.display_contract(contract)
            else:
                view.wrong_message("Contract not found.")
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_contract(self, access_token: str, contract_id: int):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            contract_data = self.get_contract_data()
            contract = contract_logic.update_contract(access_token, user_id, contract_id, contract_data)
            if contract:
                view.success_message(f"Contract '{contract.id}' updated successfully.")
            else:
                view.wrong_message("Contract not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def delete_contract(self, access_token: str, contract_id: int):
        try:
            if contract_logic.delete_contract(access_token, contract_id):
                view.success_message("Contract deleted successfully.")
            else:
                view.wrong_message("Contract not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    # Event
    def create_event(self, access_token: str):
        try:
            event_data = self.get_event_data()
            event = event_logic.create_event(access_token, event_data)
            view.success_message(f"Event '{event.title}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_events(self, access_token: str, filtered: bool):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            events = event_logic.get_events(access_token, user_id, filtered)
            view.display_events(events)
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_event(self, access_token: str, event_id: int):
        try:
            event = event_logic.get_event_by_id(event_id)
            if event:
                view.display_event(event)
            else:
                view.wrong_message("Event not found.")
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
    
    def update_event(self, access_token: str, event_id: int):
        try:
            user_info = get_user_info()
            user_id = user_info['user_id']
            event_data = self.get_event_data()
            event = event_logic.update_event(access_token, user_id, event_id, event_data)
            if event:
                view.success_message(f"Event '{event.title}' updated successfully.")
            else:
                view.wrong_message("Event not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
            
    def assign_support_to_event(self, access_token: str, event_id: int, support_id: int):
        try:
            event = event_logic.assign_support_to_event(access_token, event_id, support_id)
            if event:
                view.success_message(f"Event '{event.title}' assigned to support user {support_id}.")
            else:
                view.wrong_message("Event not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def delete_event(self, access_token: str, event_id: int):
        try:
            if event_logic.delete_event(access_token, event_id):
                view.success_message("Event deleted successfully.")
            else:
                view.wrong_message("Event not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    # Company
    def create_company(self, access_token: str):
        try:
            company_data = self.get_company_data()
            company = company_logic.create_company(access_token, company_data)
            view.success_message(f"Company '{company.name}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_companies(self, access_token: str):
        try:
            companies = company_logic.get_companies(access_token)
            view.display_companies(companies)
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
    
    def view_company(self, access_token: str, company_id: int):
        try:
            company = company_logic.get_company_by_id(company_id)
            if company:
                view.display_company(company)
            else:
                view.wrong_message("Company not found.")
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_company(self, access_token: str, company_id: int):
        try:
            company_data = self.get_company_data()
            company = company_logic.update_company(access_token, company_id, company_data)
            if company:
                view.success_message(f"Company '{company.name}' updated successfully.")
            else:
                view.wrong_message("Company not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def delete_company(self, access_token: str, company_id: int):
        try:
            if company_logic.delete_company(access_token, company_id):
                view.success_message("Company deleted successfully.")
            else:
                view.wrong_message("Company not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

main_controller = MainController()
