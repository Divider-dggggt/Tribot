import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not set")
