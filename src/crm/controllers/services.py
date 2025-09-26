from datetime import datetime
from src.auth.validators import (
    is_email_globally_unique,
    is_phone_globally_unique,
    is_username_globally_unique,
    is_valid_email,
    is_valid_password,
    is_valid_phone,
    is_valid_role_id,
    is_valid_username,
)


class DataService:
    def __init__(self, view=None):
        self.view = view

    def normalized_string(self, text: str, lower: bool = False) -> str:
        text = text.strip()
        if lower:
            text = text.lower()
        return text

    def normalized_username(self, username: str, exclude_user_id: int = None) -> str | None:
        username = self.normalized_string(username, lower=True)
        if is_valid_username(username) and is_username_globally_unique(username, exclude_user_id):
            return username
        return

    def normalized_email(self, email: str, exclude_user_id: int = None, exclude_client_id: int = None) -> str | None:
        email = self.normalized_string(email, lower=True)
        if is_valid_email(email) and is_email_globally_unique(email, exclude_user_id, exclude_client_id):
            return email
        return

    def normalized_phone(self, phone_number: str, exclude_client_id: int = None) -> str | None:
        # Here we start by normalizing the phone number so
        # it can be verified by the module phonenumbers
        phone_number = self.normalized_string(phone_number)

        # Check if phone_number is empty after normalization
        if not phone_number:
            return None

        # Verifying the first figure of the number
        x = phone_number[0]
        match x:
            # If it is a '+', it is in the right format
            # so no need to normalize any more
            case "+":
                phone_number = phone_number
            case "0":
                # If it starts with '00', we have to convert
                # it to the international format and replace
                # the '00' by the '+'
                if phone_number[1] == "0":
                    phone_number = f"+{phone_number[2:]}"
                # If it starts with '06', we change only the
                # '0' into '+33'
                elif phone_number[1] in ["6", "7"]:
                    phone_number = f"+33{phone_number[1:]}"
                else:
                    # We are not in measure to test every
                    # possible case, so we stop at the french
                    # format and if it is from another country
                    # we just try to validate it by making it
                    # start with a '+'
                    try:
                        phone_number = f"+{phone_number}"
                    except Exception as e:
                        if self.view:
                            self.view.wrong_message(
                                "Invalid phone number. \n"
                                "Try again later\n"
                                f"{e}"
                            )
                        return
            case _:
                phone_number = f"+{phone_number}"
        # Eventually we try to make it validate through
        # the module and check global uniqueness
        if is_valid_phone(phone_number) and is_phone_globally_unique(phone_number, exclude_client_id):
            return phone_number
        return

    def normalized_role_id(self, role_id: int | str) -> int | None:
        # Convert role_id if it's a string or validate if it's an int
        if isinstance(role_id, str):
            try:
                role_id = int(role_id)
            except ValueError:
                return None

        if is_valid_role_id(role_id):
            return role_id
        return

    def get_role_id_by_position(self, position: int) -> int | None:
        """Get actual role ID by position (1=management, 2=commercial, 3=support)."""
        from src.crm.models import Role
        from src.data_access.config import Session

        role_names = ["management", "commercial", "support"]
        if position < 1 or position > len(role_names):
            return None

        role_name = role_names[position - 1]

        with Session() as session:
            role = session.query(Role).filter(Role.name == role_name).first()
            return role.id if role else None

    def normalized_free_text(self, free_text: str | None) -> str | None:
        """
        Normalize a free text and prevent SQL injection by 
        removing dangerous characters and replacing single 
        quotes with double quotes.

        Can be applied to any field that is not contrained by
        strict rules, such as full name, adress, etc.
        """
        if not free_text:
            return

        forbidden_chars = ["/", "\\", "|", "$", "\"", "`", "^"]
        for w in free_text:
            if w in forbidden_chars:
                free_text = free_text.replace(w, "")
            elif w == "'":
                free_text = free_text.replace(w, "''")
        return free_text

    def treat_username_from_input(self, username: str) -> str | None:
        is_valid = False
        while not is_valid:
            user_input = input("Username: ")
            username = self.normalized_username(user_input)
            if not username:
                if self.view:
                    self.view.wrong_message(
                        "Username should be between 5 and 64 characters long.\n"
                        "and should not already be in use."
                    )
                continue
            else:
                is_valid = username
        return username

    def treat_full_name_from_input(self, full_name: str | None) -> str | None:
        if not full_name:
            full_name = input("Full name: ").strip()

        full_name = self.normalized_free_text(full_name)
        if not full_name:
            if self.view:
                self.view.wrong_message("Full name cannot be empty.")
            return self.treat_full_name_from_input(None)

        print(f"Full name: {full_name}")
        choice = input("Is this correct? (y/n): ").strip()
        match choice:
            case "y" | "Y" | "yes" | "Yes":
                return full_name
            case "n" | "N" | "no" | "No":
                return self.treat_full_name_from_input(None)
            case _:
                if self.view:
                    self.view.wrong_message(
                        "Invalid choice. \n"
                        "Try again later."
                    )
                return

    def treat_email_from_input(self, email: str | None) -> str | None:
        if not email:
            email = input("Email: ").strip()

        email = self.normalized_email(email)
        if not email:
            if self.view:
                self.view.wrong_message("Invalid email format.")
            return self.treat_email_from_input(None)

        print(f"Email: {email}")
        choice = input("Is this correct? (y/n): ").strip()
        match choice:
            case "y" | "Y" | "yes" | "Yes":
                return email
            case "n" | "N" | "no" | "No":
                return self.treat_email_from_input(None)
            case _:
                if self.view:
                    self.view.wrong_message(
                        "Invalid choice. \n"
                        "Try again later."
                    )
                return

    def treat_password_from_input(self, confirm: bool = False) -> str:
        while True:
            password = input("Password: ", password=True).strip()
            if not is_valid_password(password):
                if self.view:
                    self.view.wrong_message(
                        "Password must be at least 8 characters long, "
                        "contain at least one uppercase letter, "
                        "one lowercase letter, and one number."
                    )
                continue

            if confirm:
                confirm_password = input("Confirm password: ", password=True).strip()
                if password != confirm_password:
                    if self.view:
                        self.view.wrong_message("Passwords do not match.")
                    continue

            return password

    def normalized_date(self, date_str: str) -> datetime | None:
        """
        Normalize date strings from various formats to datetime objects.
        Supports formats: DD/MM/YYYY, YYYY-MM-DD, YYYY-MM-DD HH:MM:SS
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Common date formats to try
        date_formats = [
            "%d/%m/%Y",           # 21/12/2025
            "%d/%m/%Y %H:%M",     # 21/12/2025 14:30
            "%d/%m/%Y %H:%M:%S",  # 21/12/2025 14:30:00
            "%Y-%m-%d",           # 2025-12-21
            "%Y-%m-%d %H:%M",     # 2025-12-21 14:30
            "%Y-%m-%d %H:%M:%S",  # 2025-12-21 14:30:00
            "%d-%m-%Y",           # 21-12-2025
            "%d-%m-%Y %H:%M",     # 21-12-2025 14:30
            "%d-%m-%Y %H:%M:%S",  # 21-12-2025 14:30:00
        ]

        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue

        # If none of the formats work, return None
        if self.view:
            self.view.error_message(
                f"Invalid date format: '{date_str}'. "
                "Please use DD/MM/YYYY or YYYY-MM-DD format."
            )
        return None

    # Entity-specific validation methods

    def validate_and_normalize_user_data(self, data: dict, exclude_user_id: int = None) -> dict | None:
        """Validate and normalize all User data."""
        validated_data = {}

        # Username validation
        if 'username' in data:
            username = self.normalized_username(data['username'], exclude_user_id)
            if not username:
                if self.view:
                    self.view.error_message("Invalid or duplicate username")
                return None
            validated_data['username'] = username

        # Email validation
        if 'email' in data:
            email = self.normalized_email(data['email'], exclude_user_id=exclude_user_id)
            if not email:
                if self.view:
                    self.view.error_message("Invalid or duplicate email")
                return None
            validated_data['email'] = email

        # Full name validation
        if 'full_name' in data:
            full_name = self.normalized_free_text(data['full_name'])
            if not full_name:
                if self.view:
                    self.view.error_message("Invalid full name")
                return None
            validated_data['full_name'] = full_name

        # Role ID validation
        if 'role_id' in data:
            role_id = self.normalized_role_id(data['role_id'])
            if not role_id:
                if self.view:
                    self.view.error_message("Invalid role ID")
                return None
            validated_data['role_id'] = role_id

        # Password handling (already validated elsewhere)
        if 'password' in data:
            validated_data['password'] = data['password']
        if 'password_hash' in data:
            validated_data['password_hash'] = data['password_hash']

        # Copy other fields
        for key, value in data.items():
            if key not in validated_data and key not in ['username', 'email', 'full_name', 'role_id']:
                validated_data[key] = value

        return validated_data

    def validate_and_normalize_client_data(self, data: dict, exclude_client_id: int = None) -> dict | None:
        """Validate and normalize all Client data."""
        validated_data = {}

        # Email validation (global uniqueness)
        if 'email' in data:
            email = self.normalized_email(data['email'], exclude_client_id=exclude_client_id)
            if not email:
                if self.view:
                    self.view.error_message("Invalid or duplicate email")
                return None
            validated_data['email'] = email

        # Phone validation (global uniqueness)
        if 'phone' in data:
            phone = data['phone']
            if phone:  # Only validate if phone is provided (it's optional)
                phone = self.normalized_phone(phone, exclude_client_id)
                if not phone:
                    if self.view:
                        self.view.error_message("Invalid or duplicate phone number")
                    return None
                validated_data['phone'] = phone
            else:
                validated_data['phone'] = None

        # Full name validation
        if 'full_name' in data:
            full_name = self.normalized_free_text(data['full_name'])
            if not full_name:
                if self.view:
                    self.view.error_message("Invalid full name")
                return None
            validated_data['full_name'] = full_name

        # Date validation for Client dates
        if 'first_contact_date' in data:
            if isinstance(data['first_contact_date'], str):
                first_contact_date = self.normalized_date(data['first_contact_date'])
                if not first_contact_date:
                    if self.view:
                        self.view.error_message("Invalid first contact date format")
                    return None
                validated_data['first_contact_date'] = first_contact_date
            else:
                validated_data['first_contact_date'] = data['first_contact_date']

        if 'last_contact_date' in data:
            if isinstance(data['last_contact_date'], str):
                last_contact_date = self.normalized_date(data['last_contact_date'])
                if not last_contact_date:
                    if self.view:
                        self.view.error_message("Invalid last contact date format")
                    return None
                validated_data['last_contact_date'] = last_contact_date
            else:
                validated_data['last_contact_date'] = data['last_contact_date']

        # Copy other fields (company_id, commercial_id, etc.)
        for key, value in data.items():
            if key not in validated_data and key not in ['email', 'phone', 'full_name', 'first_contact_date', 'last_contact_date']:
                validated_data[key] = value

        return validated_data

    def validate_and_normalize_company_data(self, data: dict) -> dict | None:
        """Validate and normalize all Company data."""
        validated_data = {}

        # Company name validation
        if 'name' in data:
            name = self.normalized_free_text(data['name'])
            if not name:
                if self.view:
                    self.view.error_message("Invalid company name")
                return None
            validated_data['name'] = name

        # Copy other fields
        for key, value in data.items():
            if key not in validated_data and key not in ['name']:
                validated_data[key] = value

        return validated_data

    def validate_and_normalize_contract_data(self, data: dict) -> dict | None:
        """Validate and normalize all Contract data."""
        validated_data = {}

        # Amount validation
        if 'total_amount' in data:
            try:
                total_amount = float(data['total_amount'])
                if total_amount <= 0:
                    if self.view:
                        self.view.error_message("Total amount must be positive")
                    return None
                validated_data['total_amount'] = total_amount
            except (ValueError, TypeError):
                if self.view:
                    self.view.error_message("Invalid total amount format")
                return None

        if 'remaining_amount' in data:
            try:
                remaining_amount = float(data['remaining_amount'])
                if remaining_amount < 0:
                    if self.view:
                        self.view.error_message("Remaining amount cannot be negative")
                    return None
                validated_data['remaining_amount'] = remaining_amount
            except (ValueError, TypeError):
                if self.view:
                    self.view.error_message("Invalid remaining amount format")
                return None

        # Copy other fields
        for key, value in data.items():
            if key not in validated_data and key not in ['total_amount', 'remaining_amount']:
                validated_data[key] = value

        return validated_data

    def validate_and_normalize_event_data(self, data: dict) -> dict | None:
        """Validate and normalize all Event data."""
        validated_data = {}

        # Title validation
        if 'title' in data:
            title = self.normalized_free_text(data['title'])
            if not title:
                if self.view:
                    self.view.error_message("Invalid event title")
                return None
            validated_data['title'] = title

        # Address validation
        if 'full_address' in data:
            full_address = self.normalized_free_text(data['full_address'])
            if not full_address:
                if self.view:
                    self.view.error_message("Invalid event address")
                return None
            validated_data['full_address'] = full_address

        # Date validation
        if 'start_date' in data:
            if isinstance(data['start_date'], str):
                start_date = self.normalized_date(data['start_date'])
                if not start_date:
                    if self.view:
                        self.view.error_message("Invalid start date format")
                    return None
                validated_data['start_date'] = start_date
            else:
                validated_data['start_date'] = data['start_date']

        if 'end_date' in data:
            if isinstance(data['end_date'], str):
                end_date = self.normalized_date(data['end_date'])
                if not end_date:
                    if self.view:
                        self.view.error_message("Invalid end date format")
                    return None
                validated_data['end_date'] = end_date
            else:
                validated_data['end_date'] = data['end_date']

        # Validate that end_date > start_date if both are provided
        if 'start_date' in validated_data and 'end_date' in validated_data:
            if validated_data['end_date'] <= validated_data['start_date']:
                if self.view:
                    self.view.error_message("End date must be after start date")
                return None

        # Participant count validation
        if 'participant_count' in data:
            try:
                participant_count = int(data['participant_count'])
                if participant_count < 0:
                    if self.view:
                        self.view.error_message("Participant count cannot be negative")
                    return None
                validated_data['participant_count'] = participant_count
            except (ValueError, TypeError):
                if self.view:
                    self.view.error_message("Invalid participant count format")
                return None

        # Notes validation (optional)
        if 'notes' in data and data['notes']:
            notes = self.normalized_free_text(data['notes'])
            validated_data['notes'] = notes

        # Copy other fields (IDs, etc.)
        for key, value in data.items():
            if key not in validated_data and key not in ['title', 'full_address', 'start_date', 'end_date', 'participant_count', 'notes']:
                validated_data[key] = value

        return validated_data

