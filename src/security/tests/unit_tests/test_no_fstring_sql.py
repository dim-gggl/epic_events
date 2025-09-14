import re
from pathlib import Path


def test_no_fstring_sql_execution():
    """
    Guardrail test: forbid using f-strings inside SQL execution helpers.

    Disallows patterns like:
      - session.execute(f"SELECT ... {user_input}")
      - text(f"UPDATE ... {value}")
      - cursor.execute(f"DELETE ... {x}")

    SQLAlchemy and DB-API should always bind parameters, not interpolate.
    """
    src_root = Path(__file__).resolve().parents[3] / "src"
    assert src_root.exists(), f"Source root not found: {src_root}"

    # Regex patterns to flag unsafe f-string SQL usage
    patterns = [
        re.compile(r"\b(?:session|cursor)\s*\.\s*execute\s*\(\s*f[\"']", re.IGNORECASE),
        re.compile(r"\btext\s*\(\s*f[\"']", re.IGNORECASE),
    ]

    offenders: list[tuple[str, int, str]] = []
    for py_file in src_root.rglob("*.py"):
        # Skip this very test file
        if py_file == Path(__file__).resolve():
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            # If a file can't be read, skip but don't mask issues elsewhere
            continue

        for lineno, line in enumerate(content.splitlines(), start=1):
            for pat in patterns:
                if pat.search(line):
                    offenders.append((str(py_file), lineno, line.strip()))

    assert not offenders, (
        "Unsafe f-string SQL detected. Use bound parameters instead.\n" +
        "\n".join(f"{path}:{lineno}: {code}" for path, lineno, code in offenders)
    )

