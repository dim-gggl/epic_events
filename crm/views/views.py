import getpass
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from datetime import datetime
from rich.align import Align


from crm.views.config import epic_style, logo_style
from auth.validators import is_valid_password

PRESS_ENTER_CENTERED = Align.center(Text("Press ENTER: ", style="orange_red1"))
console = Console()
clear = console.clear
print = console.print
input = console.input

rw = {
    1: "One example",
    2: "Two examples"
}

def menu(title, columns=2, rows=3, padding1=0, padding2=6, border_style="dim dark_white", rw=rw):
    result = Table.grid(padding=(padding1, padding2))
    count_c, count_r = 0, 0
    while count_c < columns and count_r < rows:
        count_c += 1
        result.add_column()

        count_r += 1
        result.add_row(rw[count_r])

    return Panel(result, title=title, border_style=border_style)

def header(title="C.R.M.", subtitle="1.0", content="EPIC EVENTS", 
          title_style="bold orange_red1", subtitle_style="dim dark_white", 
          content_style="bold orange_red1", border_style="dim white",
          title_align="left", subtitle_align="right"):
    return Panel(
        Text.from_markup(f"[{content_style}]{content}[/]\n"
                        f"[dim]{datetime.utcnow().strftime('%d/%m/%Y')}[/]", justify="center"),
        border_style=border_style, 
        title=Text.from_markup(f"[{title_style}]{title}[/]"), 
        subtitle=Text.from_markup(f"[{subtitle}]{subtitle}[/]"), 
        title_align=title_align,
        subtitle_align=subtitle_align
    )

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
    if content2 and style2 and justify2:
        text = Text()
        text.append(content, style=style)
        text.append("\n")  
        text.append(content2, style=style2)
        text.justify = justify  # Appliquer la justification au texte principal
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


# metrics = Table(title="System", show_header=False, box=None)
# metrics.add_row("DB", "connected (epic_events_db)")
# metrics.add_row("Clients", "342")
# metrics.add_row("Contracts", "128")
# metrics_panel = Panel(metrics, border_style="magenta")

# console.clear()
# console.print(header)
# console.print(Columns([menu_panel, metrics_panel]))
# console.print("\nType a command or 'help' — Ctrl+C to quit\n")
# input()

class MainView:

    def _prompt_password(self, confirm: bool = True) -> str:
        """Prompt for a password securely (no echo)."""
        pwd = getpass.getpass("New password: ").strip()
        if not is_valid_password(pwd):
            print("Password should be at least 8 characters long\n"
                  "and contain at least one uppercase letter, one\n"
                  "lowercase letter and one digit.")
            if not confirm:
                return self._prompt_password(confirm=False)
            return self._prompt_password()
        if confirm:
            rep = getpass.getpass("Confirm password: ").strip()
            if pwd != rep:
                self.wrong_message("Passwords do not match.")
                rep2 = getpass.getpass("Confirm password: ").strip()
                if rep2 != pwd:
                    self.wrong_message("Passwords don't match.\nPlease try again.")
                    sys.exit(1)
            return pwd

    def display_login_menu(self):
        print(header())
        print(menu("Login or Register"))
        print("L - Login")
        print("R - Register")
        print("Q - Quit")
        print("\nType a command or 'help' — Ctrl+C to quit\n")
        return input()

    def display_main_menu(self):
        print(header())
        print(menu("Main menu", 2, 3))

    def display_message(self, message, style):
        clear()
        print(Panel.fit(Text(message, style=style), padding=(0, 6)), justify="center")
        print("\n\n\n")
        input(PRESS_ENTER_CENTERED)
    
    def success_message(self, message):
        self.display_message(message, "bold bright_green")

    def wrong_message(self, message):
        self.display_message(message, "bold bright_red")

    def warning_message(self, message):
        self.display_message(message, "bold bright_yellow")
    
    def get_username(self) -> str:
        return input("Username: ")
    
    def get_full_name(self) -> str:
        return input("Full name: ")
    
    def get_email(self) -> str:
        return input("Email: ")
    
    def get_password(self) -> str:
        return self._prompt_password()
    
    def get_role_id(self) -> str:
        return input("Role ID: ")

    def display_login(self, access_token, refresh_token, refresh_exp):
        console.clear()
        print(
            banner(
                    access_token, 
                    "bold italic dark_white", 
                    "center",
                    logo_style,
                    title="YOUR ACCESS TOKEN",
                    subtitle=None, 
                    title_style=logo_style,
            )
        )
        print()
        print(
            banner(
                    refresh_token, 
                    "bold italic dark_white", 
                    "center",
                    epic_style,
                    title="YOUR REFRESH TOKEN",
                    subtitle=None, 
                    title_style=epic_style
            )
        )
        print()
        exp_text = refresh_exp.strftime("%d/%m/%Y") if hasattr(refresh_exp, "strftime") else str(refresh_exp).split(" ")[0]
        print(
            Panel.fit(
                    exp_text, 
                    style="bold bright_yellow", 
                    border_style="dim white",
                    title=Text("Expiration date", style="bold bright_yellow"),
                    subtitle=None,
            ),
            justify="center"
        )
        print()

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
        clear()
        if centered:
            logo = centered_logo
        print(logo)
        if centered:
            print("C.R.M — 1.0.0", style="dim italic", justify="center")
        print("\n")
        if press_enter:
            print(press_enter_panel, justify="center")
            input()
        
    def display_commands(commands):
        screen = Table.grid()
        screen.add_column()
        screen.add_column()
        for com in commands:
            screen.add_row(f"{com}", f"{com.help}")

if __name__ == "__main__":
    # view = MainView()
    # view.display_login("ACCESS", "REFRESH", "2025-09-22")
    view = MainView()
    view.display_logo()