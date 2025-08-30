import bcrypt
import jwt

from .jwt.verify_token import verify_access_token
from .jwt.config import conn, cur
from exceptions import InvalidTokenError, OperationDeniedError
from .hashing import hash_password


def create_user(access_token: str, 
                username: str, 
                full_name: str, 
                email: str, 
                password: str, 
                role_id: int) -> None:
    """
    Create a new user in the database.

    Args:
        access_token: The access token of the current user.
        Must be a manager, otherwise an OperationDeniedError 
        is raised.
        username: The username of the new user.
        full_name: The full name of the new user.
        email: The email of the new user.
        password: The password of the new user.
        role_id: The role id of the new user.
    """
    # Verify the access token and check if the query comes from
    # a manager
    payload = verify_access_token(access_token)
    if payload is None:
        raise InvalidTokenError()
    if payload["role_id"] != 1:
        raise OperationDeniedError()

    password_hash = hash_password(password)

    # Insert the user in the database
    cur.execute(
        "INSERT INTO users (username, full_name, email, password_hash, role_id)"
        f" VALUES ({username}, {full_name}, {email}, {password_hash}, {role_id})"
    )
    conn.commit()
    print(f"✅ User '{username}' registered successfully.")
