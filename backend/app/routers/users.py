from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.core.security import admin_required, get_current_user, pwd_context
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def get_users(admin=Depends(admin_required)):
    try:
        return db.get_active_users()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch active users")


@router.get("/users/all", response_model=List[UserOut])
def get_all_users(admin=Depends(admin_required)):
    try:
        return db.get_all_users()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch users")


@router.get("/users/deactivated", response_model=List[UserOut])
def get_deactivated_users(admin=Depends(admin_required)):
    try:
        return db.get_deactivated_users()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch deactivated users")


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, admin=Depends(admin_required)):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserOut)
def create_user(user: UserCreate, admin=Depends(admin_required)):
    try:
        hashed_password = pwd_context.hash(user.password)
        return db.create_user(
            name=user.name,
            email=user.email,
            password=hashed_password,
            role=user.role.lower(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, current_user=Depends(get_current_user)):
    target_user = db.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = current_user["role"] == "admin"
    is_self = current_user["id"] == user_id

    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="You can only update your own account")

    if not is_admin and user.role is not None:
        raise HTTPException(status_code=403, detail="Only admins can change roles")

    if user.password is not None:
        if not is_admin:
            auth_user = db.get_user_by_email(current_user["email"])

            if not user.old_password:
                raise HTTPException(status_code=400, detail="Old password is required to change password")

            if not pwd_context.verify(user.old_password, auth_user["password"]):
                raise HTTPException(status_code=403, detail="Old password is incorrect")

            if pwd_context.verify(user.password, auth_user["password"]):
                raise HTTPException(status_code=400, detail="New password cannot be the same as old password")

        if is_admin and not is_self and target_user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Admin cannot change another Admin's password")

    hashed_password = pwd_context.hash(user.password) if user.password else None

    updated_user = db.update_user(
        user_id,
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role.lower() if user.role is not None else None,
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.patch("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: int, admin=Depends(admin_required)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Admin cannot deactivate their own account")

    deactivated = db.deactivate_user(user_id)
    if not deactivated:
        raise HTTPException(status_code=404, detail="User not found or already deactivated")
    return deactivated


@router.patch("/users/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(user_id: int, admin=Depends(admin_required)):
    reactivated = db.reactivate_user(user_id)
    if not reactivated:
        raise HTTPException(status_code=404, detail="User not found or not deactivated")
    return reactivated
