from src.auth.jwt.token_storage import (
    cleanup_token_file,
    get_user_info_from_token,
)
from src.crm.views.views import MainView
from src.data_access.config import Session

view = MainView()


def logout():
    try:
        user_info = get_user_info_from_token()
        if user_info:
            # Clear user's refresh token in database
            from src.crm.models import User
            try:
                with Session() as session:
                    user = session.get(User, user_info['user_id'])
                    if user:
                        user.refresh_token_hash = None
                        session.commit()
            except Exception:
                pass  # Ignore database errors during logout
    except Exception:
        pass  # Ignore token errors during logout

    # Always cleanup token file and surface failures to the caller
    try:
        cleanup_token_file(raise_on_error=True)
    except Exception as exc:
        raise RuntimeError(
            "Logout failed: unable to remove authentication token file."
        ) from exc

    view.success_message("Logout successful. Authentication session cleared.")
