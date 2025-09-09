import getpass
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.style import Style
from datetime import datetime
from rich.align import Align
from rich import box
from sqlalchemy import select

from db.config import Session
from crm.views.config import epic_style, logo_style, white
from crm.models import Client, Event
from auth.validators import is_valid_password


#########################################################
#                   Console
#########################################################
console = Console()
clear = console.clear
print = console.print

def clear_console(func):
    def wrapper(*args, **kwargs):
        clear()
        return func(*args, **kwargs)
    return wrapper

#########################################################
#                   Layout tools
#########################################################

def centered(content: Text | str, style: Style=None) -> Align:
    return Align.center(content, style=style)

PRESS_ENTER_CENTERED = centered("Press ENTER", "orange_red1")

def banner(content, 
           style, 
           justify, 
           border_style, 
           title=None, 
           subtitle=None, 
           title_style=None, 
           subtitle_style=None,
           content2=None,
           style2=None,
           justify2=None):
    """
    A function to display a header in a banner style layout.

    Args: 
        content: The body of the text we want to display.
        style: The style of the text we want to display.
        justify: The justification of the text we want to display.
        border_style: The style of the border we want to display.
        title / subtitle: These headers are actually displayed on the level
            of the frame/border. It's more like a label legend or information 
            label.
        content: The body of the text we want to display.
        title/subtitle/content/border-style: These are litterally what
            they're called after.
    """
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
    
    return Panel(
        text, 
        border_style=border_style, 
        title=panel_title, 
        subtitle=panel_subtitle
    )

def prompt(content, style="bold grey100", border_style="bright medium_spring_green"):
    """The prompt function is used to stylize the input prompt"""
    return Panel.fit(Text(content, style=style), border_style=border_style)


#########################################################
#                   MainView
#########################################################
class MainView:
    """The MainView class is used to display the main view of the application."""

    # Private methods to hide the password while promptin.
    @clear_console
    def _prompt_password(self, prompt_title: str = "Password") -> str:
        """Rich UI when available + secure fallback to getpass."""
        pwd = console.input("Password: ", password=True).strip()
        pwd_conf = console.input("Confirm password: ", password=True).strip()
        if pwd == pwd_conf:
            return pwd
        else:
            self.wrong_message("Passwords do not match.")
            return self._prompt_password()
        return console.input("Password: ", password=True)

    # Abstract methods to display messages in a consistent way.
    @clear_console
    def display_message(self, message, style=epic_style):
        print(Panel.fit(Text(message, style=style, justify="center"), padding=(1, 6)), justify="center")
        print("\n")
        print(Panel.fit(Text("Press ENTER", style=style, justify="center"), padding=(0, 6)), justify="center")
        input()

    # Abstract method to get input with style.
    @clear_console
    def input(self, prompt, password=False, justify="center"):
        if password:
            return getpass.getpass(prompt)
        return input(prompt)

    #########################################################
    #                   Messages
    #########################################################
    @clear_console
    def success_message(self, message):
        self.display_message(message, "bold dark_sea_green4")

    @clear_console
    def wrong_message(self, message):
        self.display_message(message, "bold dark_orange3")

    @clear_console
    def warning_message(self, message):
        self.display_message(message, "bold bright_yellow")
    
    #########################################################
    #                   Getters
    #########################################################
    @clear_console
    def get_username(self) -> str:
        return self.input("Username: ")
    
    @clear_console
    def get_full_name(self) -> str:
        return self.input("Full name: ")
    
    @clear_console
    def get_email(self) -> str:
        return self.input("Email: ")
    
    @clear_console
    def get_password(self) -> str:
        return self._prompt_password()
    
    @clear_console
    def get_role_id(self) -> str:
        return self.input("Role ID: ")
    
    @clear_console
    def get_phone(self) -> str:
        return self.input("Phone number: ")
    
    @clear_console
    def get_company_id(self) -> str:
        return self.input("Company ID: ")
    
    @clear_console
    def get_contract_id(self) -> str:
        return self.input("Contract ID: ")
    
    @clear_console
    def get_first_contact_date(self) -> str:
        return self.input("First contact date (format: dd/mm/yyyy): ")
    
    @clear_console
    def get_last_contact_date(self) -> str:
        return self.input("Last contact date (format: dd/mm/yyyy): ")

    @clear_console
    def get_title(self) -> str:
        return self.input("Title: ")

    @clear_console
    def get_full_address(self) -> str:
        return self.input("Full address: ")

    @clear_console
    def get_support_contact_id(self) -> str:
        return self.input("Support contact ID: ")

    @clear_console
    def get_start_date(self) -> str:
        return self.input("Start date (format: dd/mm/yyyy): ")
    
    @clear_console
    def get_end_date(self) -> str:
        return self.input("End date (format: dd/mm/yyyy): ")
    
    @clear_console
    def get_participant_count(self) -> str:
        return self.input("Participant count: ")    
    
    @clear_console
    def get_client_id(self) -> str:
        return self.input("Client ID: ")

    @clear_console
    def get_contract_id(self) -> str:
        return self.input("Contract ID: ")
    
    @clear_console
    def get_notes(self) -> str:
        return self.input("Notes: ")            

    @clear_console
    def get_commercial_id(self) -> str:
        return self.input("Commercial ID: ")
    
    @clear_console
    def get_total_amount(self) -> str:
        return self.input("Total amount: ")
    
    @clear_console
    def get_remaining_amount(self) -> str:
        return self.input("Remaining amount: ")
    
    @clear_console
    def get_is_signed(self) -> str:
        return self.input("Is signed (yes/no): ")
    
    @clear_console
    def get_is_fully_paid(self) -> str:
        return self.input("Is fully paid (yes/no): ")
    
    @clear_console
    def get_company_name(self) -> str:
        return self.input("Company name: ")

    #########################################################
    #                   Displayers
    #########################################################
    @clear_console
    def display_events(self, events):
        """Display a list of events."""
        print(banner(f"EVENTS ({len(events)})", epic_style, "center", "bold gold1"))
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column(header=Text("ID", style=epic_style), justify="center")
        table.add_column(header=Text("Title", style=epic_style), justify="center")
        table.add_column(header=Text("Start Date", style=epic_style), justify="center")
        table.add_column(header=Text("Support ID", style=epic_style), justify="center")
        for event in events:
            table.add_row(
                Text(
                    str(event.id), 
                    style="bold gold1"), 
                    Text(event.title, style="bold grey100"), 
                    Text(event.start_date.strftime("%d/%m/%Y"), 
                    style="grey100"), 
                    Text(str(event.support_contact_id or "Not assigned"), 
                    style="grey100"
                )
            )
        print(table, justify="center")

    @clear_console
    def display_event(self, event):
        """Display event details."""
        table = Table(title=Text(event.title.upper(), style=logo_style), box=box.ROUNDED, show_header=False)
        table.add_column()
        table.add_column()
        
        table.add_row(Text("ID", style=logo_style), Text(str(event.id), style="grey100"))
        table.add_row(Text("Title", style=logo_style), Text(event.title, style="grey100"))
        table.add_row(Text("Contract ID", style=logo_style), Text(str(event.contract_id), style="grey100"))
        table.add_row(
            Text("Support ID", style=logo_style), 
            Text(str(event.support_contact_id or "Not assigned"), 
            style="grey100")
        )
        table.add_row(
            Text("Start Date", style=logo_style), 
            Text(event.start_date.strftime("%d/%m/%Y"), 
            style="grey100")
        )
        table.add_row(
            Text("End Date", style=logo_style), 
            Text(event.end_date.strftime("%d/%m/%Y"), 
            style="grey100")
        )
        table.add_row(
            Text("Participants", 
            style=logo_style), 
            Text(str(event.participant_count), 
            style="grey100")
        )
        table.add_row(
            Text("Address", style=logo_style), 
            Text(event.full_address or "Not specified", 
            style="grey100")
        )
        table.add_row(Text("Notes", style=logo_style), Text(event.notes or "No notes", style="grey100"))
        
        print(table, justify="center")

    @clear_console
    def display_contracts(self, contracts):
        """Display a list of contracts."""
        print(banner(f"CONTRACTS ({len(contracts)})", white, "center", "bold gold1"))
        table = Table(box=box.MINIMAL, show_header=True)
        table.add_column(header=Text("ID", style=epic_style), justify="center"  )
        table.add_column(header=Text("Client", style=epic_style), justify="center")
        table.add_column(header=Text("Commercial", style=epic_style), justify="center")
        table.add_column(header=Text("Total Amount", style=epic_style), justify="center")
        table.add_column(header=Text("Signed", style=epic_style), justify="center")
        table.add_column(header=Text("Paid", style=epic_style), justify="center")
        for contract in contracts:
            table.add_row(
                Text(str(contract.id), style="grey100"), 
                Text(str(contract.client_id), 
                style="grey100"), 
                Text(str(contract.commercial_id), 
                style="grey100"), 
                Text(f"{contract.total_amount}€", 
                style="grey100"), 
                Text("Yes" if contract.is_signed else "No", 
                style="grey100"), 
                Text("Yes" if contract.is_fully_paid else "No", 
                style="grey100")
            )
        print(table, justify="center")

    @clear_console
    def display_contract(self, contract):
        """Display contract details."""
        table = Table(
            title=Text(f"CONTRACT #{contract.id}", 
            style=logo_style), 
            box=box.ROUNDED, 
            show_header=False
        )
        table.add_column()
        table.add_column()
        
        table.add_row(
            Text("ID", style=logo_style), 
            Text(str(contract.id), 
            style="grey100")
        )
        table.add_row(
            Text("Client ID", style=logo_style), 
            Text(str(contract.client_id), 
            style="grey100")
        )
        table.add_row(
            Text("Commercial ID", style=logo_style), 
            Text(str(contract.commercial_id), 
            style="grey100")
        )
        table.add_row(
            Text("Total Amount", style=logo_style), 
            Text(f"{contract.total_amount}€", 
            style="grey100")
        )
        table.add_row(
            Text("Remaining Amount", 
            style=logo_style), 
            Text(f"{contract.remaining_amount}€", 
            style="grey100")
        )
        table.add_row(
            Text("Signed", style=logo_style), 
            Text("Yes" if contract.is_signed else "No", 
            style="grey100")
        )
        table.add_row(
            Text("Fully Paid", style=logo_style), 
            Text("Yes" if contract.is_fully_paid else "No", 
            style="grey100")
        )
        table.add_row(
            Text("Created At", style=logo_style), 
            Text(contract.created_at.strftime("%d/%m/%Y"), 
            style="grey100")
        )
        table.add_row(
            Text("Updated At", style=logo_style), 
            Text(contract.updated_at.strftime("%d/%m/%Y"), 
            style="grey100")
        )
        table.add_row(
            Text("Events", style=logo_style), 
            Text(str(len(contract.events)), 
            style="grey100")
        )
        print(table, justify="center")

    @clear_console
    def display_users(self, users):
        """Display a list of users."""
        print(banner(f"USERS ({len(users)})", white, "center", "bold gold1"))
        table = Table(box=box.MINIMAL, show_header=True)
        table.add_column(header=Text("ID", style=epic_style), justify="center")
        table.add_column(header=Text("Username", style=epic_style), justify="center")
        table.add_column(header=Text("Role", style=epic_style), justify="center")
        for user in users:
            table.add_row(
                Text(str(user.id), 
                style="grey100"), 
                Text(user.username, 
                style="grey100"), 
                Text(str(user.role_id), 
                style="grey100")
            )
        print(table, justify="center")

    @clear_console
    def display_user(self, user):
        """Display user details."""
        table = Table(
            title=Text(user.username.upper(), 
            style=logo_style), 
            box=box.ROUNDED, 
            show_header=False
        )
        table.add_column()
        table.add_column()
        
        table.add_row(Text("ID", style=logo_style), Text(str(user.id), style="grey100"))
        table.add_row(Text("Username", style=logo_style), Text(user.username, style="grey100"))
        table.add_row(Text("Full Name", style=logo_style), Text(user.full_name, style="grey100"))
        table.add_row(Text("Email", style=logo_style), Text(user.email, style="grey100"))
        
        # Show role name instead of ID
        role_names = {1: 'Management', 2: 'Commercial', 3: 'Support'}
        role_name = role_names.get(user.role_id, f'Role {user.role_id}')
        table.add_row(Text("Role", style=logo_style), Text(f"{role_name} ({user.role_id})", style="grey100"))
        
        table.add_row(
            Text("Active", style=logo_style), 
            Text("Yes" if user.is_active else "No", 
            style="grey100"))
        table.add_row(
            Text("Created At", style=logo_style), 
            Text(user.created_at.strftime("%d/%m/%Y %H:%M"), 
            style="grey100")
        )
        table.add_row(
            Text("Updated At", style=logo_style), 
            Text(user.updated_at.strftime("%d/%m/%Y %H:%M"), 
            style="grey100")
        )
        table.add_row(
            Text("Events", style=logo_style), 
            Text(str(len(user.events)), 
            style="grey100")
        )
        
        if user.last_login:
            table.add_row(
                Text("Last Login", 
                style=logo_style), 
                Text(user.last_login.strftime("%d/%m/%Y %H:%M"), 
                style="grey100")
            )
        else:
            table.add_row(Text("Last Login", style=logo_style), Text("Never", style="grey100"))
            
        print(table, justify="center")


    @clear_console
    def display_login(self, access_token, refresh_token, refresh_exp):
        """Display login success without showing sensitive tokens."""
        
        # Show login success without exposing tokens
        print(
            banner(
                "LOGIN SUCCESSFUL",
                "bold gold1", 
                "center",
                "bold gold1",
                title="AUTHENTICATION",
                subtitle=None, 
                title_style="bold gold1",
            ),
            end="\n\n"
        )
        
        # Show token expiration info only
        exp_text = refresh_exp.strftime("%d/%m/%Y") if hasattr(refresh_exp, "strftime") else qlstr(refresh_exp).split(" ")[0]
        print(
            Panel.fit(
                f"Tokens stored securely until {exp_text}", 
                style="bold bright_green", 
                border_style="dim white",
                title=Text("Session Info", style="bold bright_green"),
                subtitle=None,
            ),
            justify="center",
            end="\n\n"
        )

    @clear_console
    def display_logo(self, press_enter: bool = True, centered: bool = True):
        with open("crm/views/logo.txt", "r") as file:
            logo_text = file.read()
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

    @clear_console
    def display_list_clients(self, clients):
        print(banner(f"CLIENTS ({len(clients)})", epic_style, "center", logo_style))
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column(header=Text("ID", style=epic_style), justify="center")
        table.add_column(header=Text("Full Name", style=epic_style), justify="center")
        table.add_column(header=Text("Commercial ID", style=epic_style), justify="center")
        for client in clients:
            table.add_row(
                Text(str(client.id), 
                style="bold gold1"), 
                Text(client.full_name, style="grey100"), 
                Text(str(client.commercial_id), 
                style="grey100")
            )
        print(table, justify="center")
        
    @clear_console
    def display_client_detail(self, access_token, client):
        self.display_details(
            access_token, 
            client.id, 
            Client, 
            fields=[
                "id", "full_name", "email", 
                "phone", "company_id", 
                "commercial_id", 
                "first_contact_date", 
                "last_contact_date"
            ]
        )
    
    @clear_console
    def display_list_events(self, events):
        for event in events:
            table = Table(
                title=Text(events.title.upper(), 
                style=epic_style), 
                box=box.MINIMAL, 
                show_header=False
            )
            table.add_column()
            table.add_column()
            table.add_row(
                Text("ID", style=epic_style), 
                Text(str(event.id), 
                style="grey100")
            )
            table.add_row(
                Text("Start Date", style=epic_style), 
                Text(event.start_date.strftime("%d/%m/%Y"), 
                style="grey100")
            )
            table.add_row(
                Text("Participant Count", 
                style=epic_style), 
                Text(str(event.participant_count), 
                style="grey100")
            )
            table.add_row(
                Text("Participant Count", 
                style=epic_style), 
                Text(str(event.participant_count), 
                style="grey100")
            )
        print(table, justify="center")

    @clear_console
    def display_event_detail(self, access_token, event_id):
        self.display_details(access_token, event_id, Event)
        
    @clear_console
    def display_details(self, access_token, obj_id, obj_class, fields=None):
        with Session() as session:
            obj = session.scalars(
                select(obj_class).filter(obj_class.id == obj_id)
            ).one_or_none()
            if not obj:
                self.wrong_message(
                    "OPERATION DENIED: Object not found."
                )
                return

            name = getattr(obj, "name", None)
            if not name:
                name = getattr(obj, "full_name", None)
            if not name:
                name = getattr(obj, "title", None)
            table = Table(
                title=Text(name.upper(), 
                style=logo_style), 
                box=box.ROUNDED, 
                show_header=False
            )
            table.add_column()
            table.add_column()
            if not fields:
                for key, value in obj.__dict__.items():
                    table.add_row(
                        Text(key.capitalize(), 
                        style=logo_style), 
                        Text(str(value), 
                        style="grey100")
                    )
                print(table, justify="center")
            else:
                for field in fields:
                    table.add_row(
                        Text(field.capitalize(), 
                        style=logo_style), 
                        Text(str(getattr(obj, field)), 
                        style="grey100")
                    )
                print(table, justify="center")
