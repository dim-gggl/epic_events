import getpass

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    # Encode the password to bytes
    password_bytes = password.encode('utf-8')

    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    """
    # Encode the password and hash to bytes
    password_bytes = password.encode('utf-8')
    password_hash_bytes = password_hash.encode('utf-8')

    # Verify the password
    return bcrypt.checkpw(password_bytes, password_hash_bytes)



if __name__ == "__main__":
    pwd = getpass.getpass("Password: ")
    print(hash_password(pwd))
