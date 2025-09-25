from sqlalchemy.orm import Session

from src.auth.permissions import login_required, require_permission
from src.auth.utils import _ensure_root
from src.crm.views.views import MainView

view = MainView()


def in_session(session: Session=None):
    if not session:
        session = Session()
    def decorator(func):
        def wrapper(*args, **kwargs):
            with session:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def require_elevated_privileges(func):
    def wrapper(*args, **kwargs):
        is_root = _ensure_root()
        if not is_root:
            view.wrong_message(
                "Only the ADMIN of the system can create a manager."
            )
            return
        return func(*args, **kwargs)
    return wrapper


require_permission = require_permission
login_required = login_required
