# requirements: pip install rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from datetime import datetime

console = Console()

header = Panel(
    Text.from_markup("[bold yellow]EPIC EVENTS[/]\n"
    f"[dim]{datetime.utcnow().strftime('%d/%m/%Y')}[/]", justify="center"),
    border_style="bright_blue", title=Text.from_markup("[bold yellow]CRM[/]"), subtitle=Text.from_markup("[dim]0.1.1[/]"), title_align="left", subtitle_align="right", expand=True)

menu = Table.grid(padding=(0,2))
menu.add_column()
menu.add_column()
menu.add_row("[b]L[/] Login", "[b]C[/] Clients")
menu.add_row("[b]R[/] Register", "[b]K[/] Contracts")
menu.add_row("[b]D[/] Demo", "[b]E[/] Events")
menu_panel = Panel(menu, title="Main menu", border_style="green")

metrics = Table(title="System", show_header=False, box=None)
metrics.add_row("DB", "connected (epic_events_db)")
metrics.add_row("Clients", "342")
metrics.add_row("Contracts", "128")
metrics_panel = Panel(metrics, border_style="magenta")

console.clear()
console.print(header)
console.print(Columns([menu_panel, metrics_panel]))
console.print("\nType a command or 'help' — Ctrl+C to quit\n")
input()
