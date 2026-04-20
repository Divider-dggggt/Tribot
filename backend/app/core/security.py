from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app import db
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def authenticate_user(email: str, password: str):
    user = db.get_user_by_email(email)
    if not user:
        return None
    if user["deactivated_at"] is not None:
        return None
    if not pwd_context.verify(password, user["password"]):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "iat": now,
        "exp": expire,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        if db.is_token_revoked(token):
            raise HTTPException(status_code=401, detail="Logged Out, Please log in again")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        token_iat = payload.get("iat")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user["deactivated_at"] is not None:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        if token_iat and user.get("password_changed_at"):
            password_changed_at = user["password_changed_at"].timestamp()
            if token_iat < password_changed_at:
                raise HTTPException(status_code=401, detail="Password changed. Please log in again")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def role_required(*roles):
    allowed_roles = {role.lower() for role in roles}

    def dependency(user=Depends(get_current_user)):
        user_role = str(user["role"]).lower()
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Access restricted to: {', '.join(roles)}")
        return user

    return dependency