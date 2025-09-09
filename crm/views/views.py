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
from constants import *


console = Console()
clear = console.clear
print = console.print

def clear_console(func):
    def wrapper(*args, **kwargs):
        console.clear()
        return func(*args, **kwargs)
    return wrapper

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
        text.justify = justify  # Apply justification to the main text
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

class MainView:
    """The MainView class is used to display the main view of the application."""

    def _prompt_password(self, prompt_title: str = "Password") -> str:
        """Rich UI when available + secure fallback to getpass."""
        use_rich = sys.stdin.isatty() and sys.stdout.isatty()
        if use_rich:
            console = Console()
            first = "Enter your password"
            second = "Confirm your password"
            renderable = prompt(first, style="bold grey100")
            renderable2 = prompt(second, style="bold ceinture")

            try:
                pwd = console.input(renderable, password=True).strip()
                pwd_conf = console.input(renderable2).strip()
                if pwd == pwd_conf:
                    return pwd
                else:
                    view.wrong_message("Passwords do not match.")
                    return self._prompt_password()
            except Exception as e:
                # Any terminal edge case → fall back
                view.wrong_message("An error occurred while entering the password.")
                return self._prompt_password()

        # Fallback stdlib
        try:
            return getpass.getpass("Password: ")
        except (Exception,):
            print("WARNING: No TTY detected; input will be visible.")
            return input("Password: ")


    def display_message(self, message, style=epic_style):
        clear()
        print(Panel.fit(Text(message, style=style, justify="center"), padding=(1, 6)), justify="center")
        print("\n")
        print(Panel.fit(Text("Press ENTER", style=style, justify="center"), padding=(0, 6)), justify="center")
        input()
    
    def input(self, prompt):
        prompt_text = Text(prompt, style="bold grey100", justify="center")
        email = Align.center(prompt_text)
        return console.input(email)
    
    def success_message(self, message):
        self.display_message(message, PANEL_STYLE_SUCCESS)

    def wrong_message(self, message):
        self.display_message(message, PANEL_STYLE_ERROR)

    def warning_message(self, message):
        self.display_message(message, PANEL_STYLE_WARNING)
    
    def get_username(self) -> str:
        return self.input("Username: ")
    
    def get_full_name(self) -> str:
        return self.input("Full name: ")
    
    def get_email(self) -> str:
        return self.input("Email: ")
    
    def get_password(self) -> str:
        return self._prompt_password()
    
    def get_role_id(self) -> str:
        return self.input("Role ID: ")
    
    def get_phone(self) -> str:
        return self.input("Phone number: ")
    
    def get_company_id(self) -> str:
        return self.input("Company ID: ")
    
    def get_contract_id(self) -> str:
        return self.input("Contract ID: ")
    
    def get_first_contact_date(self) -> str:
        return self.input(f"First contact date (format: {DATE_FORMAT}): ")
    
    def get_last_contact_date(self) -> str:
        return self.input(f"Last contact date (format: {DATE_FORMAT}): ")

    def get_title(self) -> str:
        return self.input("Title: ")

    def get_full_address(self) -> str:
        return self.input("Full address: ")

    def get_support_contact_id(self) -> str:
        return self.input("Support contact ID: ")

    def get_start_date(self) -> str:
        return self.input(f"Start date (format: {DATE_FORMAT}): ")
    
    def get_end_date(self) -> str:
        return self.input(f"End date (format: {DATE_FORMAT}): ")
    
    def get_participant_count(self) -> str:
        return self.input("Participant count: ")    
    
    def get_client_id(self) -> str:
        return self.input("Client ID: ")

    def get_contract_id(self) -> str:
        return self.input("Contract ID: ")
    
    def get_notes(self) -> str:
        return self.input("Notes: ")            

    def get_commercial_id(self) -> str:
        return self.input("Commercial ID: ")
    
    def get_total_amount(self) -> str:
        return self.input("Total amount: ")
    
    def get_remaining_amount(self) -> str:
        return self.input("Remaining amount: ")
    
    def get_is_signed(self) -> str:
        return self.input("Is signed (yes/no): ")
    
    def get_is_fully_paid(self) -> str:
        return self.input("Is fully paid (yes/no): ")
    
    def get_company_name(self) -> str:
        return self.input("Company name: ")

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
                Text(str(event.id), style=TABLE_STYLE_ID), 
                Text(event.title, style=TABLE_STYLE_CONTENT), 
                Text(event.start_date.strftime(DATE_FORMAT), 
                     style=TABLE_STYLE_CONTENT), 
                Text(str(event.support_contact_id or "Not assigned"), 
                     style=TABLE_STYLE_CONTENT)
            )
        print(table, justify="center")

    @clear_console
    def display_event(self, event):
        """Display event details."""
        table = Table(title=Text(event.title.upper(), style=logo_style), box=box.ROUNDED, show_header=False)
        table.add_column()
        table.add_column()
        
        table.add_row(Text("ID", style=logo_style), 
                      Text(str(event.id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Title", style=logo_style), 
                      Text(event.title, style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Contract ID", style=logo_style), 
                      Text(str(event.contract_id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Support ID", style=logo_style), 
                      Text(str(event.support_contact_id or "Not assigned"), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Start Date", style=logo_style), 
                      Text(event.start_date.strftime(DATE_FORMAT), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("End Date", style=logo_style), 
                      Text(event.end_date.strftime(DATE_FORMAT), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Participants", style=logo_style), 
                      Text(str(event.participant_count), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Address", style=logo_style), 
                      Text(event.full_address or "Not specified", 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Notes", style=logo_style), 
                      Text(event.notes or "No notes", 
                           style=TABLE_STYLE_CONTENT))
        
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
                Text(str(contract.id), style=TABLE_STYLE_CONTENT), 
                Text(str(contract.client_id), style=TABLE_STYLE_CONTENT), 
                Text(str(contract.commercial_id), style=TABLE_STYLE_CONTENT), 
                Text(f"{contract.total_amount}€", style=TABLE_STYLE_CONTENT), 
                Text("Yes" if contract.is_signed else "No", 
                     style=TABLE_STYLE_CONTENT), 
                Text("Yes" if contract.is_fully_paid else "No", 
                     style=TABLE_STYLE_CONTENT)
            )
        print(table, justify="center")

    @clear_console
    def display_contract(self, contract):
        """Display contract details."""
        table = Table(title=Text(f"CONTRACT #{contract.id}", style=logo_style), box=box.ROUNDED, show_header=False)
        table.add_column()
        table.add_column()
        
        table.add_row(Text("ID", style=logo_style), 
                      Text(str(contract.id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Client ID", style=logo_style), 
                      Text(str(contract.client_id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Commercial ID", style=logo_style), 
                      Text(str(contract.commercial_id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Total Amount", style=logo_style), 
                      Text(f"{contract.total_amount}€", style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Remaining Amount", style=logo_style), 
                      Text(f"{contract.remaining_amount}€", style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Signed", style=logo_style), 
                      Text("Yes" if contract.is_signed else "No", 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Fully Paid", style=logo_style), 
                      Text("Yes" if contract.is_fully_paid else "No", 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Created At", style=logo_style), 
                      Text(contract.created_at.strftime(DATE_FORMAT), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Updated At", style=logo_style), 
                      Text(contract.updated_at.strftime(DATE_FORMAT), 
                           style=TABLE_STYLE_CONTENT))
        
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
                Text(str(user.id), style=TABLE_STYLE_CONTENT), 
                Text(user.username, style=TABLE_STYLE_CONTENT), 
                Text(str(user.role_id), style=TABLE_STYLE_CONTENT)
            )
        print(table, justify="center")

    @clear_console
    def display_user(self, user):
        """Display user details."""
        table = Table(title=Text(user.username.upper(), style=logo_style), box=box.ROUNDED, show_header=False)
        table.add_column()
        table.add_column()
        
        table.add_row(Text("ID", style=logo_style), 
                      Text(str(user.id), style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Username", style=logo_style), 
                      Text(user.username, style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Full Name", style=logo_style), 
                      Text(user.full_name, style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Email", style=logo_style), 
                      Text(user.email, style=TABLE_STYLE_CONTENT))
        
        # Show role name instead of ID
        role_name = ROLE_NAMES.get(user.role_id, f"Role {user.role_id}")
        table.add_row(Text("Role", style=logo_style), 
                      Text(f"{role_name} ({user.role_id})", 
                           style=TABLE_STYLE_CONTENT))
        
        table.add_row(Text("Active", style=logo_style), 
                      Text("Yes" if user.is_active else "No", 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Created At", style=logo_style), 
                      Text(user.created_at.strftime(f"{DATE_FORMAT} %H:%M"), 
                           style=TABLE_STYLE_CONTENT))
        table.add_row(Text("Updated At", style=logo_style), 
                      Text(user.updated_at.strftime(f"{DATE_FORMAT} %H:%M"), 
                           style=TABLE_STYLE_CONTENT))
        
        if user.last_login:
            table.add_row(Text("Last Login", style=logo_style), 
                          Text(user.last_login.strftime(f"{DATE_FORMAT} %H:%M"), 
                               style=TABLE_STYLE_CONTENT))
        else:
            table.add_row(Text("Last Login", style=logo_style), 
                          Text("Never", style=TABLE_STYLE_CONTENT))
            
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
        exp_text = refresh_exp.strftime("%d/%m/%Y") if hasattr(refresh_exp, "strftime") else str(refresh_exp).split(" ")[0]
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
                Text(str(client.id), style=TABLE_STYLE_ID), 
                Text(client.full_name, style=TABLE_STYLE_CONTENT), 
                Text(str(client.commercial_id), style=TABLE_STYLE_CONTENT)
            )
        print(table, justify="center")
        
    @clear_console
    def display_client_detail(self, access_token, client):
        self.display_details(access_token, client.id, Client, fields=["id", "full_name", "email", "phone", "company_id", "commercial_id", "first_contact_date", "last_contact_date"])
    
    @clear_console
    def display_list_events(self, events):
        for event in events:
            table = Table(title=Text(events.title.upper(), style=epic_style), box=box.ROUNDED, show_header=False)
            table.add_column()
            table.add_column()
            table.add_row(Text("ID", style=epic_style), 
                          Text(str(event.id), style=TABLE_STYLE_CONTENT))
            table.add_row(Text("Start Date", style=epic_style), 
                          Text(event.start_date.strftime(DATE_FORMAT), 
                               style=TABLE_STYLE_CONTENT))
            table.add_row(Text("Participant Count", style=epic_style), 
                          Text(str(event.participant_count), 
                               style=TABLE_STYLE_CONTENT))
        print(table, justify="center")

    @clear_console
    def display_event_detail(self, access_token, event_id):
        self.display_details(access_token, event_id, Event)
        
    @clear_console
    def display_details(self, access_token, obj_id, obj_class, fields=None):
        with Session() as session:
            obj = session.scalars(select(obj_class).filter(obj_class.id == obj_id)).one_or_none()
            if not obj:
                self.wrong_message("OPERATION DENIED: Object not found.")
                return
            name = getattr(obj, "name", None)
            if not name:
                name = getattr(obj, "full_name", None)
            if not name:
                name = getattr(obj, "title", None)
            print()
            table = Table(title=Text(name.upper(), style=logo_style), box=box.ROUNDED, show_header=False)
            table.add_column()
            table.add_column()
            if not fields:
                for key, value in obj.__dict__.items():
                    table.add_row(Text(key.capitalize(), style=logo_style), 
                          Text(str(value), style=TABLE_STYLE_CONTENT))
                print(table, justify="center")
            else:
                for field in fields:
                    table.add_row(Text(field.capitalize(), style=logo_style), 
                                  Text(str(getattr(obj, field)), 
                                       style=TABLE_STYLE_CONTENT))
                print(table, justify="center")
