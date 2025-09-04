from __future__ import annotations

from typing import Callable, Any, Optional, cast
from datetime import datetime

from auth.validators import (
    is_valid_username, 
    is_valid_email, 
    is_valid_password, 
    is_valid_role_id, 
    is_valid_phone
)
from auth.jwt.verify_token import verify_access_token
from exceptions import InvalidTokenError, OperationDeniedError
from crm.views.views import MainView as view
from db.config import Session
from crm.models import Client

view = view()

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
    """
    Loop until a valid value is returned.
    - prompt: function that returns a raw input string
    - cast: convert raw string to a typed value (may raise)
    - validate: predicate on the casted value
    - required_msg: message shown if empty input
    - invalid_msg: message shown if cast/validation fails
    """
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
        if validate and not validate(value):
            view.wrong_message(invalid_msg or required_msg)
            continue
        return value


def _ask_optional(
    prompt: Callable[[], str],
    *,
    cast: Callable[[str], Any] = lambda s: s,
    strip: bool = True,
) -> Any:
    """Return possibly-empty input (cast if not empty)."""
    raw = prompt()
    if strip:
        raw = raw.strip()
    if raw == "":
        return "" if cast is str else None
    return cast(raw)


def _to_int(s: str) -> int:
    return int(s)


def _to_float(s: str) -> float:
    s_norm = s.replace(" ", "").replace(",", ".")
    return float(s_norm)


def _to_date(s: str) -> datetime:
    return datetime.strptime(s, DATE_FMT)


def _to_bool_yes_no(s: str) -> bool:
    s = s.strip().lower()
    if s in {"y", "yes", "Yes", "YES"}:
        return True
    if s in {"n", "no", "No", "NO"}:
        return False
    raise ValueError("Expected yes/no")


class MainController:

    def get_username(self) -> str:
        username = view.get_username().strip()
        if not is_valid_username(username):
            view.wrong_message("Username should be between 5 and 64 characters long.\n"
                              "and should not already be in use.")
            return self.get_username()
        return username
    
    def get_full_name(self) -> str:
        full_name = view.get_full_name().strip()
        return full_name

    def get_email(self) -> str:
        email = view.get_email().strip()
        if not is_valid_email(email):
            view.wrong_message("Invalid email address.")
            return self.get_email()
        return email
        
    def get_password(self) -> str:
        password = view._prompt_password().strip()
        if not is_valid_password(password):
            view.wrong_message("Password should be at least 8 characters long\n"
                              "must contain at least one uppercase letter, one\n"
                              "lowercase letter and one digit.")
            return self.get_password()
        return password

    def get_role_id(self) -> int:
        role_id = int(view.get_role_id().strip())
        if not is_valid_role_id(role_id):
            view.wrong_message("Invalid role id.")
            return self.get_role_id()
        return role_id

    def get_access_token_payload(self) -> dict:
        access_token = _ask(
            view.get_access_token, 
            required_msg="Access token cannot be empty.",
            invalid_msg="Invalid Access Token."
        )
        payload = verify_access_token(access_token)
        return payload

    def get_client_id(self) -> int:
        client_id = _ask(
            view.get_client_id,
            cast=_to_int,
            required_msg="Client ID cannot be empty.",
            invalid_msg="Client ID must be an integer.",
        )
        return client_id
    
    def get_commercial_id(self) -> int:

        commercial_id = _ask(
            view.get_commercial_id,
            cast=_to_int(n=None),
            required_msg="All collaborators have an ID.",
            invalid_msg="Commercial ID must be a positive integer.",
        )
        return commercial_id

    def get_participant_count(self) -> int:
        participant_count = _ask(
            view.get_participant_count,
            cast=_to_int,
            required_msg="The ID of the commercial collaborator.",
            invalid_msg="Commercial ID must be a positive integer.",
        )
        return participant_count

    def get_client_data(self) -> dict:
        full_name = _ask(
            view.get_full_name,
            required_msg="Full name is required.",
        )

        email = _ask(
            view.get_email,
            required_msg="Email is required.",
            invalid_msg="Invalid email address.",
            validate=is_valid_email,
        )

        phone = _ask(
            view.get_phone,
            required_msg="Phone number is required.",
            invalid_msg="Invalid phone number. Please try again.",
            validate=is_valid_phone,
        )

        company_id = _ask(
            view.get_company_id,
            cast=_to_int,
            required_msg="Company ID is required.",
            invalid_msg="Company ID must be an integer.",
        )

        first_contact_date = _ask(
            view.get_first_contact_date,
            cast=_to_date,
            required_msg="The date of the first contact with the client.",
            invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
        )

        last_contact_date = _ask(
            view.get_last_contact_date,
            cast=_to_date,
            required_msg="The date of the last contact with the client.",
            invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
        )

        return {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "company_id": company_id,
            "first_contact_date": first_contact_date,
            "last_contact_date": last_contact_date,
        }

    def get_company_info(self) -> dict:
        name = _ask(
            view.get_company_name,
            required_msg="Company name cannot be empty.",
        )
        return {"name": name}

    def get_contract_data(self, commercial_id: int=None) -> dict:
        client_id = _ask(
            view.get_client_id,
            cast=_to_int,
            required_msg="Client ID cannot be empty.",
            invalid_msg="Must be associated to a client.",
        )
        if commercial_id:
            commercial_id = commercial_id
        else:
            commercial_id = _ask(
                view.get_commercial_id,
                cast=_to_int,
                required_msg="Commercial ID cannot be empty.",
                invalid_msg="Must be associated to a commercial user.",
            )

        total_amount = _ask(
            view.get_total_amount,
            cast=_to_float,
            required_msg="A contract must have a total amount.",
            invalid_msg="Total amount must be a positive number.",
        )

        remaining_amount = _ask(
            view.get_remaining_amount,
            cast=_to_float,
            required_msg="Can be set to 0",
            invalid_msg="Remaining amount must be a positive number or 0.",
        )

        is_signed = _ask(
            view.get_is_signed,
            cast=_to_bool_yes_no,
            required_msg="We must know the status of a contract.",
            invalid_msg="Bad input, expected 'yes' or 'no'.",
        )

        is_fully_paid = _ask(
            view.get_is_fully_paid,
            cast=_to_bool_yes_no,
            required_msg="We must know the payment status of a contract.",
            invalid_msg="Bad input, expected 'yes' or 'no'.",
        )

        return {
            "client_id": client_id,
            "commercial_id": commercial_id,
            "total_amount": total_amount,
            "remaining_amount": remaining_amount,
            "is_signed": is_signed,
            "is_fully_paid": is_fully_paid,
        }

    def get_event_data(self) -> dict:
        contract_id = _ask(
            view.get_contract_id,
            cast=_to_int,
            required_msg="An event is related to a signed contract.",
            invalid_msg="Contract ID must be an integer.",
        )

        support_contact_id = _ask(
            view.get_support_contact_id,
            cast=_to_int,
            required_msg="Support contact ID cannot be empty.",
            invalid_msg="Must be associated to a support user.",
        )

        title = _ask(
            view.get_title,
            required_msg="Title of the event to be displayed.",
        )

        full_address = _ask_optional(
            view.get_full_address, cast=str
        ) or ""

        start_date = _ask(
            view.get_start_date,
            cast=_to_date,
            required_msg=f"Start date is required (format: {DATE_FMT}).",
            invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
        )

        end_date = _ask(
            view.get_end_date,
            cast=_to_date,
            required_msg=f"End date is required (format: {DATE_FMT}).",
            invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
        )

        if end_date < start_date:
            view.wrong_message("End date must be on or after start date.")
            end_date = _ask(
                view.get_end_date,
                cast=_to_date,
                required_msg=f"End date is required (format: {DATE_FMT}).",
                invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
            )
            if end_date < start_date:
                view.wrong_message("End date must be on or after start date.")
                end_date = _ask(
                    view.get_end_date,
                    cast=_to_date,
                    required_msg=f"End date is required (format: {DATE_FMT}).",
                    invalid_msg=f"Invalid date. Expected format: {DATE_FMT}.",
                )

        participant_count = _ask(
            view.get_participant_count,
            cast=_to_int(),
            required_msg="Participant count is required.",
            invalid_msg="Participant count must be an integer.",
        )

        notes = _ask_optional(view.get_notes, cast=str) or ""

        return {
            "contract_id": contract_id,
            "support_contact_id": support_contact_id,
            "title": title,
            "full_address": full_address,
            "start_date": start_date,
            "end_date": end_date,
            "participant_count": participant_count,
            "notes": notes,
        }