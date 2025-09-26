from datetime import datetime

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from src.crm.views.config import epic_style, logo_style, white_style

#########################################################
#                   Console
#########################################################

console = Console()
clear = console.clear
print = console.print


def clear_console(func):
    def wrapper(*args, **kwargs):
        console.clear()
        return func(*args, **kwargs)
    return wrapper


#########################################################
#                   Layout tools
#########################################################


def centered(content: Text | str, style: Style = None) -> Align:
    return Align.center(content, style=style)


def banner(content, style, justify, border_style, title=None, subtitle=None,
           title_style=None, subtitle_style=None, content2=None, style2=None,
           justify2=None):
    """A function to display a header in a banner style layout."""
    if content2:
        text = Text()
        text.append(content, style=style)
        text.append("\n")
        text.append(content2, style=style2)
        text.justify = justify
    else:
        text = Text(content, style=style, justify=justify)

    panel_title = None
    panel_subtitle = None

    if title and title_style:
        panel_title = Text(title, style=title_style)
    elif title:
        panel_title = title

    if subtitle and subtitle_style:
        panel_subtitle = Text(subtitle, style=subtitle_style)
    elif subtitle:
        panel_subtitle = subtitle

    return Panel(text, border_style=border_style, title=panel_title,
                 subtitle=panel_subtitle)


def prompt(content, style="bold grey100",
           border_style="bright medium_spring_green"):
    """The prompt function is used to stylize the input prompt"""
    return Panel.fit(Text(content, style=style), border_style=border_style)


#########################################################
#                   MainView
#########################################################


class MainView:
    """The MainView class is used to display the main view of the application."""

    #########################################################
    #                   Entity Field Definitions
    #########################################################

    ENTITY_FIELDS = {
        "user": {
            "list": ["id", "username", "role_id"],
            "details": [
                "id", "username", "full_name", "email", "role_id",
                "is_active", "created_at", "updated_at", "last_login"
            ]
        },
        "client": {
            "list": ["id", "full_name", "commercial_id"],
            "details": [
                "id", "full_name", "email", "phone", "company_id",
                "commercial_id", "first_contact_date", "last_contact_date"
            ]
        },
        "contract": {
            "list": [
                "id", "client_id", "commercial_id", "total_amount",
                "is_signed", "is_fully_paid"
            ],
            "details": [
                "id", "client_id", "commercial_id", "total_amount",
                "remaining_amount", "is_signed", "is_fully_paid",
                "created_at", "updated_at"
            ]
        },
        "event": {
            "list": ["id", "title", "start_date", "support_contact_id"],
            "details": [
                "id", "title", "contract_id", "support_contact_id",
                "start_date", "end_date", "participant_count",
                "full_address", "notes"
            ]
        },
        "company": {
            "list": ["id", "name"],
            "details": ["id", "name", "created_at"]
        }
    }

    #########################################################
    #                   Messages
    #########################################################

    @clear_console
    def display_message(self, message, style=epic_style, press_enter=False):
        self.display_logo(press_enter=False, centered=True)
        print(Panel.fit(
            Text(message, style=style, justify="center"),
            padding=(1, 6)
        ),
            justify="center"
        )
        if press_enter:
            print("\n")
            print(Panel.fit(
                Text("Press ENTER", style=style, justify="center"),
                padding=(0, 6)
            ),
                justify="center"
            )
            input(f"{'':^}")


    @clear_console
    def success_message(self, message):
        self.display_message(message, "bold dark_sea_green4", press_enter=False)

    @clear_console
    def wrong_message(self, message):
        self.display_message(message, "bold dark_orange3")

    @clear_console
    def warning_message(self, message):
        self.display_message(message, "bold bright_yellow")

    @clear_console
    def error_message(self, message):
        self.display_message(message, "bold dark_red")

    @clear_console
    def sure_to_delete(self, obj):
        return console.input(
            f"Are you sure you want to delete "
            f"<{obj.__class__.__name__} #{obj.id}>? (yes/no): "
        )

    #########################################################
    #                   Input Methods
    #########################################################

    def _get_input(self, prompt_text, password=False):
        """Generic input method."""
        self.display_logo(press_enter=False, centered=True)
        print(Panel.fit(
            Text(prompt_text, style=white_style, justify="center"),
            padding=(0, 3)
            ),
            justify="center"
        )
        return console.input(f"{'':^}", password=password)

    @clear_console
    def input(self, prompt, password=False, justify="center"):
        if password:
            return input(prompt, password=True)
        return input(prompt)

    @clear_console
    def prompt_for_value(self, key):
        return self.input(f"{key}: ")

    @clear_console
    def get_input(self, prompt_text: str) -> str:
        """Generic input method for text fields."""
        return self._get_input(prompt_text)

    # Specialized input methods for common fields
    @clear_console
    def get_username(self) -> str:
        return self._get_input("Username")

    @clear_console
    def get_full_name(self) -> str:
        return self._get_input("Full name")

    @clear_console
    def get_email(self) -> str:
        return self._get_input("Email")

    @clear_console
    def get_password(self) -> str:
        return self._get_input("Password", password=True)

    @clear_console
    def get_password_with_confirmation(self) -> str:
        """Get password with confirmation."""
        while True:
            password = self._get_input("Password", password=True)
            confirm_password = self._get_input("Confirm password", password=True)

            if password == confirm_password:
                return password
            else:
                self.wrong_message("Passwords do not match. Please try again.")

    @clear_console
    def get_role_id(self) -> str:
        return self._get_input(
            "Role ID (1=management, 2=commercial, 3=support)"
        )

    @clear_console
    def get_list_fields(self, fields: list[str]) -> list[str]:
        """Asks the user to select fields to display from a list."""
        print(Panel(
            Text("Please select the fields to display:",
                 justify="center", style=epic_style)
        ))

        table = Table(box=box.MINIMAL, show_header=False)
        table.add_column(style="bold gold1", justify="right")
        table.add_column(style="grey100")

        for i, field in enumerate(fields, 1):
            table.add_row(f"[{i}]", field)

        print(table, justify="center")
        print("\n")

        return console.input(
            Panel.fit(
                Text(
                    "Enter the numbers of the fields, "
                    "separated by commas (e.g., 1,3,4)\n"
                    "Press ENTER to select all.",
                    justify="center",
                    style="dim white"
                )
            )
        )

    # Auto-generated getters for other fields
    def __getattr__(self, name):
        """Auto-generate getters for field inputs."""
        if name.startswith('get_'):
            field_name = name[4:]  # Remove 'get_' prefix

            # Convert underscore to space and capitalize
            display_name = field_name.replace('_', ' ').title()

            # Add format hints for specific fields
            format_hints = {
                'date': ' (format: dd/mm/yyyy)',
                'amount': ' (in euros)',
                'count': ' (number)',
                'id': ' (number)',
                'phone': ' (international format: +33...)',
                'email': ' (example@domain.com)'
            }

            for hint_key, hint_text in format_hints.items():
                if hint_key in field_name:
                    display_name += hint_text
                    break

            @clear_console
            def dynamic_getter():
                return self._get_input(display_name)

            return dynamic_getter

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    #########################################################
    #                   Private Generic Methods
    #########################################################

    def _get_entity_display_name(self, obj):
        """Get display name for an entity."""
        name = getattr(obj, "name", None)
        if not name:
            name = getattr(obj, "full_name", None)
        if not name:
            name = getattr(obj, "title", None)
        if not name:
            name = getattr(obj, "username", None)
        if not name:
            name = obj.__class__.__name__
        return name

    def _format_field_value(self, obj, field):
        """Format a field value for display."""
        value = getattr(obj, field, "")

        # Handle datetime fields
        if any(datefield in field for datefield in [
            "created_at", "updated_at", "last_login",
            "first_contact_date", "last_contact_date",
            "start_date", "end_date"
        ]):
            if isinstance(value, datetime):
                return value.strftime("%d/%m/%Y - %H:%M")

        # Handle special cases
        if field in ["is_signed", "is_fully_paid", "is_active"]:
            return "Yes" if value else "No"

        return str(value) if value is not None else ""

    def _display_details(self, obj, fields=None, title=None):
        """Generic method to display object details."""
        display_name = title or self._get_entity_display_name(obj)

        table = Table(
            title=Text(display_name.upper(), style=logo_style),
            box=box.ROUNDED,
            show_header=False
        )
        table.add_column(style=logo_style)
        table.add_column(style="grey100")

        if fields:
            for field in fields:
                formatted_value = self._format_field_value(obj, field)
                table.add_row(
                    field.replace("_", " ").capitalize(),
                    formatted_value
                )
        else:
            # Display all non-private attributes
            for key, value in obj.__dict__.items():
                if not key.startswith("_"):
                    formatted_value = self._format_field_value(obj, key)
                    table.add_row(
                        key.replace("_", " ").capitalize(),
                        formatted_value
                    )

        print(table, justify="center")

    def _display_list(self, objects, fields, title=None):
        """Generic method to display a list of objects."""
        if not objects:
            print("No items to display")
            return

        entity_name = title or f"{objects[0].__class__.__name__.upper()}S"
        print(banner(
            f"{entity_name} ({len(objects)})",
            epic_style,
            "center",
            "bold gold1"
        ))

        table = Table(box=box.MINIMAL, show_header=True)
        for field in fields:
            table.add_column(
                header=Text(field.replace("_", " ").title(),
                            style=epic_style),
                justify="center"
            )

        for obj in objects:
            row_values = []
            for field in fields:
                formatted_value = self._format_field_value(obj, field)
                row_values.append(Text(formatted_value, style=white_style))
            table.add_row(*row_values)

        print(table, justify="center")

    #########################################################
    #                   Public Display Methods
    #########################################################

    # User display methods
    @clear_console
    def display_users(self, users):
        """Display a list of users."""
        self._display_list(users, self.ENTITY_FIELDS["user"]["list"],
                           "USERS")

    @clear_console
    def display_user(self, user):
        """Display user details."""
        self._display_details(user, self.ENTITY_FIELDS["user"]["details"])

    # Client display methods
    @clear_console
    def display_clients(self, clients):
        """Display a list of clients."""
        self._display_list(clients, self.ENTITY_FIELDS["client"]["list"],
                           "CLIENTS")

    @clear_console
    def display_client_details(self, client):
        """Display client details."""
        self._display_details(client, self.ENTITY_FIELDS["client"]["details"])

    # Legacy methods for compatibility
    def display_client_detail(self, access_token, client):
        self.display_client_details(client)

    @clear_console
    def display_list_clients(self, clients):
        """Legacy method - redirects to display_clients."""
        self.display_clients(clients)

    # Contract display methods
    @clear_console
    def display_contracts(self, contracts):
        """Display a list of contracts."""
        self._display_list(contracts, self.ENTITY_FIELDS["contract"]["list"],
                           "CONTRACTS")

    @clear_console
    def display_contract(self, contract):
        """Display contract details."""
        self._display_details(contract, self.ENTITY_FIELDS["contract"]["details"])

    # Event display methods
    @clear_console
    def display_events(self, events):
        """Display a list of events."""
        self._display_list(events, self.ENTITY_FIELDS["event"]["list"],
                           "EVENTS")

    @clear_console
    def display_event(self, event):
        """Display event details."""
        self._display_details(event, self.ENTITY_FIELDS["event"]["details"])

    # Company display methods
    @clear_console
    def display_companies(self, companies):
        """Display a list of companies."""
        self._display_list(companies, self.ENTITY_FIELDS["company"]["list"],
                           "COMPANIES")

    @clear_console
    def display_company(self, company):
        """Display company details."""
        self._display_details(company, self.ENTITY_FIELDS["company"]["details"])

    # Generic public methods
    @clear_console
    def display_details(self, obj, fields=None):
        """Public method to display object details."""
        self._display_details(obj, fields)

    @clear_console
    def display_list(self, objects, fields=None):
        """Public method to display a list of objects."""
        if fields is None and objects:
            entity_type = objects[0].__class__.__name__.lower()
            fields = self.ENTITY_FIELDS.get(entity_type, {}).get("list", [])
        self._display_list(objects, fields)

    #########################################################
    #                   Login and Logo
    #########################################################

    @clear_console
    def display_login(self, access_token, refresh_token, refresh_exp):
        """Display login success without showing sensitive tokens."""
        self.display_logo(press_enter=False, centered=True)
        print(
            banner(
                "LOGIN SUCCESSFUL",
                white_style,
                "center",
                "bold gold1",
                title="AUTHENTICATION",
                title_style=epic_style,
            ),
            end="\n\n"
        )

    @clear_console
    def display_logo(self, press_enter: bool = True, centered: bool = True):
        try:
            with open("src/crm/views/logo.txt") as file:
                logo_text = file.read()
        except FileNotFoundError:
            logo_text = "EPIC EVENTS CRM"

        logo = Text(logo_text)
        logo.stylize(epic_style, 0, 145)
        logo.stylize(logo_style, 145, 147)
        logo.stylize(epic_style, 147, 176)
        logo.stylize(logo_style, 176, 190)
        logo.stylize(epic_style, 191, 194)
        logo.stylize(logo_style, 194, 221)
        logo.stylize(epic_style, 222, 225)
        logo.stylize(logo_style, 226, -1)

        press_enter_panel = Panel.fit(
            Text("Press ENTER", style=epic_style, justify="center"),
            border_style="dim white",
            padding=(0, 6)
        )
        centered_logo = Align.center(logo)
        if centered:
            logo = centered_logo
        print(logo)
        if centered:
            print("C.R.M — 1.0.0", style="dim italic", justify="center")
        print("\n")
        if press_enter:
            print(press_enter_panel, justify="center")
            input()


view = MainView()
