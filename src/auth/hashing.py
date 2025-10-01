import getpass

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Password string to hash

    Returns:
        Hashed password as string

    Raises:
        ValueError: If password is too long (> 72 bytes when encoded)
    """
    # Encode the password to bytes
    password_bytes = password.encode('utf-8')

    # Bcrypt has a 72-byte limit
    if len(password_bytes) > 72:
        raise ValueError(
            "Password too long for bcrypt "
            "(max 72 bytes when UTF-8 encoded)"
        )

    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to verify against

    Returns:
        True if password matches hash, False otherwise

    Note:
        Returns False for any bcrypt errors (invalid hash format, etc.)
        rather than raising exceptions for security reasons.
    """
    try:
        # Encode the password and hash to bytes
        password_bytes = password.encode('utf-8')
        password_hash_bytes = password_hash.encode('utf-8')

        # Verify the password
        return bcrypt.checkpw(password_bytes, password_hash_bytes)
    except (ValueError, TypeError):
        # Invalid hash format or other bcrypt errors
        # Return False for security (constant-time behavior)
        return False



if __name__ == "__main__":
    pwd = getpass.getpass("Password: ")
    print(hash_password(pwd))
