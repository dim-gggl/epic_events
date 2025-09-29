import ctypes
import os

from src.crm.views.views import view

def get_secret_key() -> str:
    value = os.environ.get("SECRET_KEY")
    if not value:
        view.wrong_message("SECRET_KEY is not set")
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
            view.wrong_message("This command must be run as root.")
            return False
        return True
    else:
        if os.geteuid() != 0:
            view.wrong_message("This command must be run with root privileges.")
            return False
        return True
