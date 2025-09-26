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
        if not user_info:
            view.wrong_message("No active session found.")
            return

        # Do not alter last_login on logout; it reflects last successful login
        with Session():
            pass  # No-op DB interaction retained for symmetry
        cleanup_token_file()

        view.success_message("Logout successful. Authentication session cleared.")

    except Exception as e:
        view.wrong_message(f"Logout failed: {str(e)}")
