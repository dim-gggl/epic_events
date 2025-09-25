import ctypes
import os

from rich.console import Console

console = Console()
print = console.print

def get_secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if not value:
        print("[red]SECRET_KEY is not set[/red]")
    return value


def _ensure_root() -> bool:
    """Check administrative privileges without terminating the process.

    Returns True when the current process has administrative privileges, False otherwise.

    - On POSIX (macOS/Linux), require EUID == 0 (i.e., 'sudo ...').
    - On Windows, require an elevated process (Administrator).
    """
    if os.name == "nt":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            # If we cannot determine admin status, treat as not elevated
            is_admin = False

        if not is_admin:
            print("[red]This command must be run as root.[/red]")
            return False
        return True
    else:
        if os.geteuid() != 0:
            print("[red]This command must be run with root privileges.[/red]")
            return False
        return True
