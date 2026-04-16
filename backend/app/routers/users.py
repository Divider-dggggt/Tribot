from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.core.security import admin_required, get_current_user, pwd_context
from app.schemas.user import UserCreate, UserOut, UserUpdate, DeactivatedUserOut

router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def get_users(admin=Depends(admin_required)):
    try:
        return db.get_all_users()
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch users")


@router.get("/users/deactivated", response_model=List[DeactivatedUserOut])
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
            role=user.role,
        )

    except Exception as e:
        error_text = str(e).lower()

        if "email" in error_text and "unique" in error_text:
            raise HTTPException(status_code=409, detail="Email already exists")

        raise HTTPException(status_code=500, detail="Failed to create user")


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, current_user=Depends(get_current_user)):
    target_user = db.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = current_user["role"] == "Admin"
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

        if is_admin and not is_self and target_user["role"] == "Admin":
            raise HTTPException(status_code=403, detail="Admin cannot change another Admin's password")

    hashed_password = pwd_context.hash(user.password) if user.password else None

    try:
        updated_user = db.update_user(
            user_id,
            name=user.name,
            email=user.email,
            password=hashed_password,
            role=user.role,
        )

    except Exception as e:
        error_text = str(e).lower()

        if "email" in error_text and "unique" in error_text:
            raise HTTPException(status_code=409, detail="Email already exists")

        raise HTTPException(status_code=500, detail="Failed to update user")

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.patch("/users/{user_id}")
def deactivate_user(user_id: int, admin=Depends(admin_required)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Admin cannot deactivate their own account")

    deactivated = db.deactivate_user(user_id)
    if not deactivated:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": deactivated["id"],
        "message": "User deactivated successfully"
    }


@router.patch("/users/{user_id}/reactivate")
def reactivate_user(user_id: int, admin=Depends(admin_required)):
    reactivated = db.reactivate_user(user_id)
    if not reactivated:
        raise HTTPException(status_code=404, detail="Deactivated user not found")

    return {
        "id": reactivated["id"],
        "message": "User reactivated successfully"
    }

