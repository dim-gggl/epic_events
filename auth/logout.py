from auth.jwt.token_storage import get_user_info, cleanup_token_file
from db.config import Session
from crm.models import User
from crm.views.views import MainView
from datetime import datetime, timezone
from sentry.observability import log_authentication_event, log_error, log_operation


view = MainView()


def logout():
    try:
        user_info = get_user_info()
        if not user_info:
            view.wrong_message("No active session found.")
            return

        user_id = user_info['user_id']
        with Session() as session:
            user = session.query(User).filter(User.id == user_id).one_or_none()
            if user:
                user.last_login = datetime.now(timezone.utc)
                session.commit()

            else:
                log_authentication_event(
                    "logout_warning",
                    success=False,
                    context={"reason": "user_not_found", "user_id": user_id}
                )
            cleanup_token_file()

        view.success_message("Logout successful. Authentication session cleared.")

    except Exception as e:
        view.wrong_message(f"Logout failed: {str(e)}")    