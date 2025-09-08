from auth.jwt.token_storage import get_user_info, cleanup_token_file
from db.config import Session
from crm.models import User
from crm.views.views import MainView
from datetime import datetime

view = MainView()


def logout():
    with Session() as session:
        user_id = get_user_info()['user_id']
        user = session.query(User).filter(User.id == user_id).one_or_none()
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        cleanup_token_file()
    view.success_message("Logout successful. Authentication session cleared.")    