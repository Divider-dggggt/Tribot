from datetime import datetime

from pydantic import BaseModel, EmailStr, constr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str


class UserCreate(UserBase):
    password: constr(min_length=6, max_length=72)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    old_password: str | None = None
    password: str | None = None
    role: str | None = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    deactivated_at: datetime | None = None
