from collections.abc import Callable
from datetime import datetime
from typing import Any

import sentry_sdk

from src.auth.jwt.token_storage import get_user_info_from_token
from src.auth.login import login as login_user
from src.auth.logout import logout as logout_user
from src.auth.validators import (
    is_valid_email,
    is_valid_password,
    is_valid_phone,
    is_valid_role_id,
    is_valid_username,
)
from src.business_logic.client_logic import client_logic
from src.business_logic.company_logic import company_logic
from src.business_logic.contract_logic import contract_logic
from src.business_logic.event_logic import event_logic
from src.business_logic.user_logic import user_logic
from src.views.views import MainView

view = MainView()

DATE_FMT_DATE = "%d/%m/%Y"
DATE_FMT_DATETIME = "%d/%m/%Y %H:%M"
# Backwards-compat alias used in messages and other parsers
DATE_FMT = DATE_FMT_DATE

def _ask(
    prompt: Callable[[], str],
    *,
    cast: Callable[[str], Any] = lambda s: s,
    validate: Callable[[Any], bool] | None = None,
    required_msg: str,
    invalid_msg: str | None = None,
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

def _parse_datetime_with_default(s: str, default_hour: int, default_minute: int) -> datetime:
    """Parse flexible date input. Accepts "dd/mm/yyyy HH:MM" or "dd/mm/yyyy".

    When time part is missing, uses provided default hour/minute.
    """
    try:
        return datetime.strptime(s, DATE_FMT_DATETIME)
    except Exception:
        # Try date-only and inject default time
        d = datetime.strptime(s, DATE_FMT_DATE)
        return d.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)


def _to_start_datetime(s: str) -> datetime:
    return _parse_datetime_with_default(s, 0, 0)


def _to_end_datetime(s: str) -> datetime:
    return _parse_datetime_with_default(s, 23, 59)


def _to_date(s: str) -> datetime:
    """Date-only parser kept for client/contact dates."""
    return datetime.strptime(s, DATE_FMT_DATE)

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
    validate: Callable[[Any], bool] | None = None,
    invalid_msg: str | None = None,
    strip: bool = True,
) -> Any:
    while True:
        raw = prompt()
        if strip:
            raw = raw.strip()
        if not raw:
            return
        try:
            value = cast(raw)
        except Exception:
            if invalid_msg:
                view.wrong_message(invalid_msg)
            continue
        if not validate or validate(value):
            return value
        if invalid_msg:
            view.wrong_message(invalid_msg)

class MainController:

    # Authentication
    def login(self, username, password):
        # Password must be entered via secure prompt (no CLI plaintext)
        login_user(username, password)
        sentry_sdk.capture_message(f"User {username} logged in.")

    def logout(self):
        logout_user()
        sentry_sdk.capture_message("User logged out.")

    # Session helper
    def _get_session_user_or_warn(self) -> dict | None:
        info = get_user_info_from_token()
        if not info:
            view.wrong_message("Your session is missing or expired. Please login again.")
            return None
        return info

    # User input gathering
    def get_user_data(self, username: str | None = None, full_name: str | None = None,
                      email: str | None = None, role_id: int | None = None) -> dict:
        if not username:
            username = _ask(
                view.get_username,
                required_msg="Username is required.",
                validate=is_valid_username
            )
        if not full_name:
            full_name = _ask(
                view.get_full_name,
                required_msg="Full name is required."
            )
        if not email:
            email = _ask(
                view.get_email,
                required_msg="Email is required.",
                validate=is_valid_email
            )
        password = _ask(
            view._prompt_password,
            required_msg="Password is required.",
            validate=is_valid_password
        )
        if role_id is None:
            role_id = _ask(
                view.get_role_id,
                cast=_to_int,
                required_msg="Role ID is required.",
                validate=is_valid_role_id
            )
        return {
            "username": username,
            "full_name": full_name,
            "email": email,
            "password": password,
            "role_id": role_id
            }

    def get_user_update_data(self, username: str | None = None, full_name: str | None = None,
                             email: str | None = None, role_id: int | None = None) -> dict:
        data: dict = {}
        if username is not None:
            data["username"] = username
        else:
            val = _ask_optional(view.get_username, validate=is_valid_username)
            if val:
                data["username"] = val
        if full_name is not None:
            data["full_name"] = full_name
        else:
            val = _ask_optional(view.get_full_name)
            if val:
                data["full_name"] = val
        if email is not None:
            data["email"] = email
        else:
            val = _ask_optional(view.get_email, validate=is_valid_email, invalid_msg="Invalid email address.")
            if val:
                data["email"] = val
        if role_id is not None:
            data["role_id"] = role_id
        else:
            val = _ask_optional(view.get_role_id, cast=_to_int, validate=is_valid_role_id,
                                invalid_msg="Role ID must be an integer between 1 and 3.")
            if val is not None:
                data["role_id"] = val
        return data

    def get_client_data(self,
                        full_name: str,
                        email: str,
                        phone: str,
                        company_id: str,
                        first_contact_date: str,
                        last_contact_date: str) -> dict:
        if not full_name:
            full_name = _ask(
                view.get_full_name,
                required_msg="Full name is required."
            )
        if not email:
            email = _ask(
                view.get_email,
                required_msg="Email is required.",
                invalid_msg="Invalid email address.",
                validate=is_valid_email
            )
        if not phone:
            phone = _ask(
                view.get_phone,
                required_msg="Phone number is required.",
                invalid_msg="Invalid phone number. Please try again.",
                validate=is_valid_phone
            )
        if not company_id:
            company_id = _ask(
                view.get_company_id,
                cast=_to_int,
                required_msg="Company ID is required.",
                invalid_msg="Company ID must be an integer."
            )
        if not first_contact_date:
            first_contact_date = _ask(
                view.get_first_contact_date,
                cast=_to_date,
                required_msg="The date of the first contact with the client.",
                invalid_msg=f"Invalid date. Expected format: {DATE_FMT}."
            )
        if not last_contact_date:
            last_contact_date = _ask(
                view.get_last_contact_date,
                cast=_to_date,
                required_msg="The date of the last contact with the client.",
                invalid_msg=f"Invalid date. Expected format: {DATE_FMT}."
             )
        return {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "company_id": company_id,
            "first_contact_date": first_contact_date,
            "last_contact_date": last_contact_date}

    def get_contract_data(self,
                          client_id: str,
                          commercial_id: str,
                          total_amount: str,
                          remaining_amount: str,
                          is_signed: str,
                          is_fully_paid: str) -> dict:
        if not client_id:
            client_id = _ask(
                view.get_client_id,
                cast=_to_int,
                required_msg="Client ID is required."
            )
        else:
            # Convert string to int if provided as parameter
            client_id = int(client_id)
        if not commercial_id:
            commercial_id = _ask(
                view.get_commercial_id,
                cast=_to_int,
                required_msg="Commercial ID is required."
            )
        else:
            # Convert string to int if provided as parameter
            commercial_id = int(commercial_id)
        if not total_amount:
            total_amount = _ask(
                view.get_total_amount,
                cast=_to_float,
                required_msg="Total amount is required."
            )
        else:
            # Convert string to float if provided as parameter
            total_amount = float(total_amount)
        if not remaining_amount:
            remaining_amount = _ask(
                view.get_remaining_amount,
                cast=_to_float,
                required_msg="Remaining amount is required."
            )
        else:
            # Convert string to float if provided as parameter
            remaining_amount = float(remaining_amount)
        if not is_signed:
            is_signed = _ask(
                view.get_is_signed,
                cast=_to_bool_yes_no,
                required_msg="Is signed is required."
            )
        else:
            # Convert string to boolean if provided as parameter
            is_signed = is_signed.lower() in ('true', '1', 'yes', 'y')
        if not is_fully_paid:
            is_fully_paid = _ask(
                view.get_is_fully_paid,
                cast=_to_bool_yes_no,
                required_msg="Is fully paid is required."
            )
        else:
            # Convert string to boolean if provided as parameter
            is_fully_paid = is_fully_paid.lower() in ('true', '1', 'yes', 'y')
        return {
            "client_id": client_id,
            "commercial_id": commercial_id,
            "total_amount": total_amount,
            "remaining_amount": remaining_amount,
            "is_signed": is_signed,
            "is_fully_paid": is_fully_paid
        }

    def get_event_data(self,
                       contract_id: str,
                       title: str,
                       full_address: str,
                       support_contact_id: str,
                       start_date: str,
                       end_date: str,
                       participant_count: str,
                       notes: str) -> dict:
        # Normalize provided CLI values when present (parse/cast) before prompting
        if start_date:
            try:
                start_date = _to_start_datetime(start_date) if isinstance(start_date, str) else start_date
            except Exception:
                view.wrong_message("Invalid date. Expected format: dd/mm/yyyy or dd/mm/yyyy HH:MM.")
                start_date = None
        if end_date:
            try:
                end_date = _to_end_datetime(end_date) if isinstance(end_date, str) else end_date
            except Exception:
                view.wrong_message("Invalid date. Expected format: dd/mm/yyyy or dd/mm/yyyy HH:MM.")
                end_date = None
        if not contract_id:
            contract_id = _ask(
                view.get_contract_id,
                cast=_to_int,
                required_msg="Contract ID is required."
            )
        if not title:
            title = _ask(
                view.get_title,
                required_msg="Title is required."
            )
        if not full_address:
            full_address = _ask(
                view.get_full_address,
                required_msg="Full address is required."
            )
        if not support_contact_id:
            support_contact_id = _ask_optional(
                view.get_support_contact_id,
                cast=_to_int
            )
        if not start_date:
            start_date = _ask(
                view.get_start_date,
                cast=_to_start_datetime,
                required_msg="Start date is required.",
                invalid_msg="Invalid date. Expected format: dd/mm/yyyy or dd/mm/yyyy HH:MM."
            )
        if not end_date:
            end_date = _ask(
                view.get_end_date,
                cast=_to_end_datetime,
                required_msg="End date is required.",
                invalid_msg="Invalid date. Expected format: dd/mm/yyyy or dd/mm/yyyy HH:MM."
            )
        # Ensure end date is strictly after start date at datetime precision
        if end_date <= start_date:
            view.wrong_message("End date must be after start date (consider adding a time).")
            end_date = _ask(
                view.get_end_date,
                cast=_to_end_datetime,
                required_msg="End date is required.",
                invalid_msg="Invalid date. Expected format: dd/mm/yyyy or dd/mm/yyyy HH:MM.",
                validate=lambda d: d > start_date,
            )
        if not participant_count:
            participant_count = _ask(
                view.get_participant_count,
                cast=_to_int,
                required_msg="Participant count is required."
            )
        if not notes:
            notes = _ask_optional(
                view.get_notes
            )
        return {
            "contract_id": contract_id,
            "title": title,
            "full_address": full_address,
            "support_contact_id": support_contact_id,
            "start_date": start_date,
            "end_date": end_date,
            "participant_count": participant_count,
            "notes": notes
        }

    def get_company_data(self, name: str | None = None) -> dict:
        if not name:
            name = _ask(
                view.get_company_name,
                required_msg="Company name is required."
            )
        return {"name": name}

    # CRUD methods
    # User
    def create_user(self, access_token: str, username: str | None, full_name: str | None,
                    email: str | None, role_id: int | None):
        try:
            user_data = self.get_user_data(username, full_name, email, role_id)
            user = user_logic.create_user(access_token, user_data)
            view.success_message(f"User '{user.username}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_users(self, access_token: str, management: bool, commercial: bool, support: bool):
        try:
            users = user_logic.get_users(access_token)
            if management:
                users = [user for user in users if user.role_id == 1]
            if commercial:
                users = [user for user in users if user.role_id == 2]
            if support:
                users = [user for user in users if user.role_id == 3]
            view.display_users(users)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_user(self, access_token: str, user_id: int):
        try:
            user = user_logic.get_user_by_id(access_token, user_id)
            if user:
                view.display_user(user)
            else:
                view.wrong_message("User not found.")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_user(self, access_token: str, user_id: int, username: str | None,
                    full_name: str | None, email: str | None, role_id: int | None):
        try:
            user_data = self.get_user_update_data(username, full_name, email, role_id)
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
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
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
    def create_client(self,
                      access_token: str,
                      full_name: str,
                      email: str,
                      phone: str,
                      company_id: str,
                      first_contact_date: str,
                      last_contact_date: str):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            client_data = self.get_client_data(full_name,
                                               email,
                                               phone,
                                               company_id,
                                               first_contact_date,
                                               last_contact_date)
            client = client_logic.create_client(access_token, client_data, user_id)
            view.success_message(f"Client '{client.full_name}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_clients(self, access_token: str, filtered: bool):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            clients = client_logic.get_clients(access_token, user_id, filtered)
            view.display_list_clients(clients)
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_client(self, access_token: str, client_id: int):
        try:
            client = client_logic.get_client_by_id(access_token, client_id)
            if client:
                view.display_client_detail(access_token, client)
            else:
                view.wrong_message("Client not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_client(self, access_token: str, client_id: int,
                      full_name: str | None, email: str | None, phone: str | None,
                      company_id: str | None, first_contact_date: str | None, last_contact_date: str | None):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            client_data = self.get_client_data(full_name, 
                                               email, phone, 
                                               company_id, 
                                               first_contact_date, 
                                               last_contact_date)
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
            client_logic.delete_client(access_token, client_id)
            view.success_message("Client deleted successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
            return
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")
            return

    # Contract
    def create_contract(self,
                        access_token: str,
                        client_id: str,
                        commercial_id: str,
                        total_amount: str,
                        remaining_amount: str,
                        is_signed: str,
                        is_fully_paid: str):
        try:
            # Check if user has management role
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            if user_info['role_id'] != 1:  # 1 = management role
                view.wrong_message("Only management users can create contracts.")
                return

            contract_data = self.get_contract_data(client_id,
                                                   commercial_id,
                                                   total_amount,
                                                   remaining_amount,
                                                   is_signed,
                                                   is_fully_paid)

            # Validate that client and commercial are already related
            from src.data_access.config import Session
            from src.data_access.repository import client_repository
            with Session() as session:
                client = client_repository.get_by_id(contract_data['client_id'], session)
                if not client:
                    view.wrong_message("Client not found.")
                    return
                if client.commercial_id != contract_data['commercial_id']:
                    view.wrong_message("The client and commercial must already be related.")
                    return

            contract = contract_logic.create_contract(access_token, contract_data)
            view.success_message(
                f"Contract for client '{contract.client.full_name}' created successfully."
            )
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_contracts(self, access_token: str, filtered: bool):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            contracts = contract_logic.get_contracts(access_token, user_id, filtered)
            view.display_contracts(contracts)
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_contract(self, access_token: str, contract_id: int):
        try:
            contract = contract_logic.get_contract_by_id(access_token, contract_id)
            if contract:
                view.display_contract(contract)
            else:
                view.wrong_message("Contract not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_contract(self, access_token: str, contract_id: int,
                        client_id: str | None, commercial_id: str | None, total_amount: str | None,
                        remaining_amount: str | None, is_signed: str | None, is_fully_paid: str | None):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            contract_data = self.get_contract_data(client_id, 
                                                   commercial_id, 
                                                   total_amount, 
                                                   remaining_amount, 
                                                   is_signed, 
                                                   is_fully_paid)
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
    def create_event(self, access_token: str,
                     contract_id: str | None, title: str | None, full_address: str | None,
                     support_contact_id: str | None, start_date: str | None, end_date: str | None,
                     participant_count: str | None, notes: str | None):
        try:
            event_data = self.get_event_data(contract_id, title, full_address, support_contact_id,
                                             start_date, end_date, participant_count, notes)
            event = event_logic.create_event(access_token, event_data)
            view.success_message(f"Event '{event.title}' created successfully.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def list_events(self, access_token: str, filtered: bool, unassigned: bool = False):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            events = event_logic.get_events(access_token, user_id, filtered, unassigned_only=unassigned)
            view.display_events(events)
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def view_event(self, access_token: str, event_id: int):
        try:
            event = event_logic.get_event_by_id(access_token, event_id)
            if event:
                view.display_event(event)
            else:
                view.wrong_message("Event not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_event(self, access_token: str, event_id: int,
                     contract_id: str | None, title: str | None, full_address: str | None,
                     support_contact_id: str | None, start_date: str | None, end_date: str | None,
                     participant_count: str | None, notes: str | None):
        try:
            user_info = self._get_session_user_or_warn()
            if not user_info:
                return
            user_id = user_info['user_id']
            event_data = self.get_event_data(contract_id, title, full_address, support_contact_id,
                                             start_date, end_date, participant_count, notes)
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
    def create_company(self, access_token: str, name: str | None):
        try:
            company_data = self.get_company_data(name)
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
            company = company_logic.get_company_by_id(access_token, company_id)
            if company:
                view.display_company(company)
            else:
                view.wrong_message("Company not found.")
        except (PermissionError, ValueError) as e:
            view.wrong_message(str(e))
        except Exception as e:
            view.wrong_message(f"An unexpected error occurred: {e}")

    def update_company(self, access_token: str, company_id: int, name: str | None):
        try:
            company_data = self.get_company_data(name)
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
