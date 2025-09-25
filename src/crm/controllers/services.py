from src.auth.validators import (
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

    def normalized_username(self, username: str) -> str | None:
        username = self.normalized_string(username, lower=True)
        if is_valid_username(username):
            return username
        return

    def normalized_email(self, email: str) -> str | None:
        email = self.normalized_string(email, lower=True)
        if is_valid_email(email):
            return email
        return

    def normalized_phone(self, phone_number: str) -> str | None:
        # Here we start by normalizing the phone number so
        # it can be verified by the module phonenumbers
        phone_number = self.normalized_string(phone_number)

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
                elif phone_number[1] == "6":
                    phone_number = f"+33{phone_number[2:]}"
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
        # the module
        if is_valid_phone(phone_number):
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

