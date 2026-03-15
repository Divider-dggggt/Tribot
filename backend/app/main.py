from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr
from . import db
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, text
from passlib.context import CryptContext
import os
from typing import Optional, List, Dict
from app.services.severity_flagging import flag_high_severity

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/app_db")

app = FastAPI()

# Enable CORS for React frontend
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)


# Password hashing
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class ProcessCaseRequest(BaseModel):
    case_id: int

class ProcessCaseResponse(BaseModel):
    case_id: int
    soap_summary: str

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str  # Admin, Clinician, Researcher


class UserCreate(UserBase):
    #password: str  # plain password, will be hashed before storing
    password: constr(min_length=6, max_length=72)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime

# Request model
class CaseCreate(BaseModel):
    user_id: int
    case_details: str

# Response model
class CaseFullOut(BaseModel):
    case_id: int
    user_id: int
    case_details: str
    severity_flagged: bool
    soap_summary: str
    ats_classification: int
    confidence_score: float
    severity_flags: Optional[Dict[int, str]] = None

# Routes

@app.get("/users", response_model=List[UserOut])
def get_users():
    """Fetch all users"""
    try:
        users = db.get_all_users()
        return users
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch users")


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    """Fetch user by ID"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate):
    """Create a new user"""
    try:
        hashed_password = pwd_context.hash(user.password)  # no 72-byte limit
        #hashed_password = pwd_context.hash(user.password[:72])
        new_user = db.create_user(
            name=user.name,
            email=user.email,
            password=hashed_password,
            role=user.role
        )
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate):
    """Update user by ID"""
    hashed_password = pwd_context.hash(user.password) if user.password else None
    updated_user = db.update_user(
        user_id,
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete user by ID"""
    deleted = db.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": deleted["id"]}


def soap_summary(text: str) -> str:
    return f"SOAP summary for..."  #to be replaced by actual


def classification_algo(text: str) -> dict:
    severity_info = flag_high_severity(text) # to be replace by actual
    traige_res = triage_classification(text) # to be replace by actual

    ##Some logic between two models and then return the results below replacing demo values

    return {
        "model_id": 1,
        "ats_category": 2,
        "confidence_score": 0.85,
        "severity_flags": False
    }


@app.post("/cases", response_model=CaseFullOut)
def create_case_endpoint(case: CaseCreate):
    try:
        soap_text = soap_summary(case.case_details)

        classification_res = classification_algo(case.case_details)
        severity_info = classification_res["severity_flags"]

        new_case = db.add_case(
            user_id=case.user_id,
            case_details=case.case_details,
            severity_flagged=severity_info["is_high_severity"]
        )
        case_id = new_case["case_id"]

        db.add_soap_summary(case_id, soap_text) #might be replace with anonymise()??

        db.add_classification_model(
            case_id=case_id,
            model_id=classification_res["model_id"],
            ats_classification=classification_res["ats_category"],
            confidence_score=classification_res["confidence_score"]
        )

        severity_flags_dict = {}
        if severity_info["is_high_severity"]:
            for label, ats in severity_info["matched_categories"].items():
                reason_text = ", ".join(severity_info["flags"].get(label, []))
                db.add_severity_flag(case_id, ats, reason_text)
                severity_flags_dict[ats] = reason_text

        return {
            "case_id": case_id,
            "user_id": new_case["user_id"],
            "case_details": new_case["case_details"],
            "severity_flagged": new_case["severity_flagged"],
            "soap_summary": soap_text,
            "ats_classification": classification_res["ats_category"],
            "confidence_score": classification_res["confidence_score"],
            "severity_flags": severity_flags_dict or None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")


@app.get("/")
def health():
    """Health check"""
    return {"status": "ok"}
