from cryptography.fernet import Fernet

from app.core.config import ENCRYPTION_KEY

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not set")

cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_text(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()


def decrypt_text(value: str) -> str:
    return cipher.decrypt(value.encode()).decode()
