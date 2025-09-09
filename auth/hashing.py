import bcrypt
import getpass


def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode('utf-8')
    password_hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, password_hash_bytes)



if __name__ == "__main__":
    pwd = getpass.getpass("Password: ")
    print(hash_password(pwd))