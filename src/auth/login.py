from datetime import UTC, datetime

from sqlalchemy import select

from src.auth.hashing import verify_password
from src.auth.jwt.generate_token import generate_token
from src.auth.jwt.token_storage import store_token
from src.crm.models import User
from src.crm.views.views import MainView
from src.data_access.config import Session

view = MainView()

def login(username: str,
		  password: str | None = None,
		  ) -> tuple[str, str, datetime, bytes]:
	"""
	Authenticate a user and return access and refresh tokens.

	Returns (access_token, raw_refresh, refresh_expiration, refresh_hash).
	Raises InvalidUsernameError or InvalidPasswordError on failure.
	"""
	view = MainView()
	if not username:
		username = view.get_username().strip()
	if not password:
		password = view.get_password()

	with Session() as session:
		user = session.query(User).filter(User.username==username).first()

		if not user:
			view.wrong_message("Unknown username.")
			return

		if not verify_password(password, user.password_hash):
			view.wrong_message("Wrong password.")
			return

		access_token, raw_refresh, refresh_exp, refresh_hash = generate_token(user.id, user.role_id)
		user.refresh_token_hash = refresh_hash.decode("utf-8")
		
		# Update last_login at successful authentication
		user.last_login = datetime.now(UTC)
		session.commit()

		store_token(access_token, raw_refresh, refresh_exp, user.id, user.role_id)
		view.success_message(f"Login successful. Connected as {user.username}")
		view.display_login(access_token, raw_refresh, refresh_exp)

		return access_token, raw_refresh, refresh_exp, refresh_hash
