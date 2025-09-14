from rich.text import Text

import src.cli.main as cli


def test_determine_line_type():
    assert cli._determine_line_type("Usage: prog [OPTIONS]") == "usage"
    assert cli._determine_line_type("Commands:") == "section_header"
    assert cli._determine_line_type("  cmd  desc") == "command"
    assert cli._determine_line_type("    --opt  help") == "option"
    assert cli._determine_line_type("") == "empty"
    assert cli._determine_line_type("other") == "default"


def test_format_help_with_styles_smoke():
    help_text = "\n".join([
        "Usage: cli [OPTIONS]",
        "",
        "Commands:",
        "  foo   Do foo",
        "",
        "Options:",
        "    --bar  Set bar",
        "Other text"
    ])
    out = cli.format_help_with_styles(help_text)
    assert isinstance(out, Text)


