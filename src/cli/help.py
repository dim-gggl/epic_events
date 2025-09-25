from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.crm.views.config import epic_style, logo_style
from src.crm.views.views import clear_console

LOGO_PATH = Path("src/crm/views/logo.txt")
console = Console()


@clear_console
def build_logo_text() -> Text:
    text = LOGO_PATH.read_text(encoding="utf-8")
    t = Text(text, no_wrap=True)
    t.stylize(epic_style, 0, 145)
    t.stylize(logo_style, 145, 147)
    t.stylize(epic_style, 147, 176)
    t.stylize(logo_style, 176, 191)
    t.stylize(epic_style, 191, 194)
    t.stylize(logo_style, 194, 221)
    t.stylize(epic_style, 221, 225)
    t.stylize(logo_style, 225, -1)
    return t


def _format_usage_line(line: str, styled_text: Text) -> None:
    """Format a usage line with specific styling 
    for command and options."""
    styled_text.append('Usage: ', style=epic_style)
    parts = line.split(' ', 2)
    if len(parts) > 1:
        styled_text.append(parts[1] + ' ', style=logo_style)
    if len(parts) > 2:
        styled_text.append(parts[2], style="bold grey100")
    styled_text.append('\n')


def _format_section_header(line: str, styled_text: Text) -> None:
    """Format section headers (lines ending with ':')."""
    styled_text.append(line, style=epic_style)
    styled_text.append('\n')


def _format_command_line(line: str, styled_text: Text) -> None:
    """Format command lines (indented with 2 spaces, not 4)."""
    parts = line.strip().split(None, 1)
    styled_text.append('  ', style="bold grey100")

    if parts:
        styled_text.append(parts[0], style=logo_style)
        if len(parts) > 1:
            styled_text.append('  ', style="bold grey100")
            styled_text.append(parts[1], style="bold grey100")
    else:
        styled_text.append(line, style="bold grey100")

    styled_text.append('\n')


def _format_option_line(line: str, styled_text: Text) -> None:
    """Format option lines (indented with 4 spaces, containing -- or -)."""
    styled_text.append(line, style="bold grey100")
    styled_text.append('\n')


def _format_empty_line(styled_text: Text) -> None:
    """Format empty lines."""
    styled_text.append('\n')


def _format_default_line(line: str, styled_text: Text) -> None:
    """Format any other line with default styling."""
    styled_text.append(line, style="bold grey100")
    styled_text.append('\n')


def _determine_line_type(line: str) -> str:
    """Determine the type of line for appropriate formatting."""
    line_stripped = line.strip()
    possibilities = {
        'usage': line_stripped.startswith('Usage:'),
        'section_header': line_stripped.endswith(':') and not line.startswith('  '),
        'command': line.startswith('  ') and not line.startswith('    '),
        'option': '--' in line_stripped or line_stripped.startswith('-') and line.startswith('    '),
        'empty': not line_stripped,
        'default': True,
    }
    for key, value in possibilities.items():
        if value:
            return key
    return 'default'


def format_help_with_styles(help_text: str) -> Text:
    """
    Format help text with rich styling for better readability.
    
    Args:
        help_text: Raw help text from Click command
        
    Returns:
        Rich Text object with applied styling
    """
    styled_text = Text()
    lines = help_text.split('\n')

    for line in lines:
        line_type = _determine_line_type(line)

        match line_type:
            case 'usage':
                _format_usage_line(line, styled_text)
            case 'section_header':
                _format_section_header(line, styled_text)
            case 'command':
                _format_command_line(line, styled_text)
            case 'option':
                _format_option_line(line, styled_text)
            case 'empty':
                _format_empty_line(styled_text)
            case _:
                _format_default_line(line, styled_text)

    return styled_text

@clear_console
def render_help_with_logo(ctx: click.Context) -> None:
    raw_logo = LOGO_PATH.read_text(encoding="utf-8")
    max_logo_width = max((len(line) for line in raw_logo.splitlines()), default=40)
    logo = build_logo_text()
    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, width=max_logo_width + 2)
    grid.add_column(ratio=1)
    left = Padding(logo, (0, 1))

    # Create help text manually to avoid rich-click conflicts
    help_lines = []
    help_lines.append(f"Usage: {ctx.command.name} [OPTIONS]")
    if ctx.command.help:
        help_lines.append("")
        help_lines.append(ctx.command.help)

    if hasattr(ctx.command, 'commands') and ctx.command.commands:
        help_lines.append("")
        help_lines.append("Commands:")
        for name, cmd in ctx.command.commands.items():
            help_lines.append(
                f"  {name:<15} {cmd.short_help or cmd.help or ''}"
            )

    if hasattr(ctx.command, 'params') and ctx.command.params:
        help_lines.append("")
        help_lines.append("Options:")
        for param in ctx.command.params:
            if isinstance(param, click.Option):
                opts = ', '.join(param.opts)
                help_lines.append(f"  {opts:<20} {param.help or ''}")

    help_text = '\n'.join(help_lines)
    help_content = format_help_with_styles(help_text) if help_text else Text(
        "No help available"
    )
    right = Panel(help_content,
                  box=box.ROUNDED,
                  border_style=epic_style,
                  padding=(1, 2),
                  title=Text("HELP",
                  style=epic_style),
                  title_align="left")
    grid.add_row(left, right)
    console.print(grid)

def attach_help(group: click.Group) -> None:
    @group.command("help")
    @click.argument("command", required=False)
    @click.pass_context
    def _help(ctx: click.Context, command: str | None) -> None:
        if command:
            cmd = group.get_command(ctx, command)
            if not cmd:
                console.print(f"Unknown command: {command}")
                parent_ctx = click.Context(group, parent=ctx.parent)
                render_help_with_logo(parent_ctx)
            else:
                cmd_ctx = click.Context(cmd, parent=ctx)
                render_help_with_logo(cmd_ctx)
        else:
            parent_ctx = click.Context(group, parent=ctx.parent)
            render_help_with_logo(parent_ctx)

def _epic_help_callback(ctx, param, value):
    if value:
        render_help_with_logo(ctx)
        ctx.exit()


def epic_help(cmd):
    return click.option('-h',
                        '--help',
                        is_flag=True,
                        is_eager=True,
                        expose_value=False,
                        callback=_epic_help_callback,
                        help='Show this message and exit.')(cmd)
