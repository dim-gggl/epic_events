from rich.text import Text
from rich.style import Style
from rich.console import Console
from rich.align import Align
from rich.panel import Panel
from rich import print, rule

console = Console()
with open("crm/views/logo.txt", "r") as file:
    logo_text = file.read()

logo_style = Style(color="bright_green", bold=True)
epic_style = Style(color="orange_red1", bold=True)
dim_style = Style(color="white", bold=False, italic=True, dim=True)
logo = Text(logo_text)
logo.stylize(epic_style, 0, 145)
logo.stylize(logo_style, 145, 147)
logo.stylize(epic_style, 147, 176)
logo.stylize(logo_style, 176, 190)
logo.stylize(epic_style, 191, 194)
logo.stylize(logo_style, 194, 221)
logo.stylize(epic_style, 222, 225)
logo.stylize(logo_style, 226, -1)
LOGO = logo

press_enter_panel = Panel.fit(
    Text("Press ENTER", style=epic_style, justify="center"),
    border_style="dim white",
    padding=(0, 6)    
)
centered_logo = Align.center(logo)
console.clear()
console.print(centered_logo)
console.print("C.R.M — 1.0.0", style=dim_style, justify="center")
console.print("\n")
console.print(press_enter_panel, justify="center")
console.input()
