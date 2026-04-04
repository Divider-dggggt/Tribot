from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.core.security import authenticate_user, create_access_token, get_current_user, oauth2_scheme
from app.schemas.auth import LoginRequest
from app.schemas.user import UserOut

router = APIRouter()


@router.post("/login")
def login(user: LoginRequest):
    auth_user = authenticate_user(user.email, user.password)

    if not auth_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "user_id": auth_user["id"],
        "role": auth_user["role"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": auth_user["role"],
    }


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    db.revoke_token(token)
    return {"msg": "Logged out successfully"}
