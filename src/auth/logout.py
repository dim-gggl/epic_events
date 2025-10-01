from src.auth.jwt.token_storage import (
    cleanup_token_file,
    get_user_info_from_token,
)
from src.crm.views.views import MainView
from src.data_access.config import Session
from src.crm.models import User

view = MainView()


def logout():
    try:
        user_info = get_user_info_from_token()
        if user_info:
            # Clear user"s refresh token in database
            try:
                with Session() as session:
                    user = session.query(User).filter(
                        User.id == user_info["id"]
                    ).first()

                    if user:
                        user.refresh_token_hash = None
                        session.commit()
     
            except Exception as e:
                view.error_message(f"Database error during logout: {e}")
                return

    except Exception as err:
        view.error_message(f"Error during logout: {err}")
        return

    # Always cleanup token file and surface failures to the caller
    try:
        cleanup_token_file(raise_on_error=True)
    except Exception as exc:
        raise RuntimeError(
            "Logout failed: unable to remove authentication token file."
        ) from exc

    view.success_message("Logout successful. Authentication session cleared.")
