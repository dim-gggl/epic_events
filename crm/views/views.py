# requirements: pip install rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from datetime import datetime

console = Console()
clear = console.clear
print = console.print

rw = {
    1: "One example",
    2: "Two examples"
}

def menu(title, columns=2, rows=3, padding1=0, padding2=6, border_style=dim_gray):
    result = Table.grid(padding=(padding1, padding2))
    count_c, count_r = 0, 0
    while count_c < columns and count_r < rows:
        count_c += 1
        result.add_column()

        count_r += 1
        result.add_row(rw[count_r])

    return Panel(result, title=title, border_style=style)

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


# metrics = Table(title="System", show_header=False, box=None)
# metrics.add_row("DB", "connected (epic_events_db)")
# metrics.add_row("Clients", "342")
# metrics.add_row("Contracts", "128")
# metrics_panel = Panel(metrics, border_style="magenta")

console.clear()
console.print(header)
console.print(Columns([menu_panel, metrics_panel]))
console.print("\nType a command or 'help' — Ctrl+C to quit\n")
input()

class MainView:

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