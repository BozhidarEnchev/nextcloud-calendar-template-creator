from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from cryptography.fernet import Fernet
from decouple import config

ph = PasswordHasher()


def hash_password(plain: str) -> str:
    hashed = ph.hash(plain)
    return hashed


def verify_password(hashed: str, plain: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError):
        return False


def encrypt_secret(plain_secret: str) -> bytes:
    encrypted_secret = Fernet(config("FERNET_KEY")).encrypt(plain_secret.encode("utf-8"))
    return encrypted_secret


def decrypt_secret(password: bytes) -> bytes:
    decrypted_password = Fernet(config("FERNET_KEY")).decrypt(password)
    return decrypted_password
