from src.auth.jwt.token_storage import get_user_info_from_token, cleanup_token_file
from src.data_access.config import Session
from src.crm.models import User
from src.views.views import MainView
from datetime import datetime, timezone



view = MainView()


def logout():
    try:
        user_info = get_user_info_from_token()
        if not user_info:
            view.wrong_message("No active session found.")
            return

        user_id = user_info['user_id']
        with Session() as session:
            user = session.query(User).filter(User.id == user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                session.commit()
            cleanup_token_file()

        view.success_message("Logout successful. Authentication session cleared.")

    except Exception as e:
        view.wrong_message(f"Logout failed: {str(e)}")    