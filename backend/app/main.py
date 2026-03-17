from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from pydantic import BaseModel, EmailStr, constr
from . import db
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from passlib.context import CryptContext
import os
from typing import Optional, List
from app.services.triage_classifier.severity_flagging import flag_high_severity
import json
from jose import JWTError, jwt

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
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

security = HTTPBearer()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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

class CaseCreate(BaseModel):
    user_id: int
    case_details: str

class CaseFullOut(BaseModel):
    case_id: int
    #user_id: int
    #case_details: str
    severity_flagged: bool
    soap_summary: str
    ats_classification: int
    confidence_score: float
    flagged_keywords: str

def authenticate_user(email: str, password: str):

    user = db.get_user_by_email(email)

    if not user:
        return None

    if not pwd_context.verify(password, user["password"]):
        return None

    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/login")
def login(user: LoginRequest):

    auth_user = authenticate_user(user.email, user.password)

    if not auth_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "user_id": auth_user["id"],
        "role": auth_user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": auth_user["role"]
    }

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        if db.is_token_revoked(token):
            raise HTTPException(status_code=401, detail="Logged Out, Please log in again")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found or deleted")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def role_required(*roles):
    def dependency(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"{roles} access required")
        return user
    return dependency

def admin_required(user=Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def clinician_required(user=Depends(get_current_user)):
    if user["role"] != "Clinician":
        raise HTTPException(status_code=403, detail="Clinician access required")
    return user

@app.get("/me", response_model=UserOut)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

@app.post("/logout")
def logout(user=Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    # Add token to revoked_tokens
    db.revoke_token(token)
    return {"msg": "Logged out successfully"}

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
def create_user(user: UserCreate, admin=Depends(admin_required)):
    """Create a new user"""
    try:
        hashed_password = pwd_context.hash(user.password)
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
    #to call SOAP Summary model (Boqian)
    soap_text = ""
    return soap_text

def triage_classification(text: str) -> str:
    return f"triage classification call..."  #to call classification model

def classification_algo(text: str) -> dict:
    severity_info = flag_high_severity(text) # to call severity_flagged (Rasheed)
    traige_res = triage_classification(text) # to call Classification (Roshni)

    ## Assuming traige_classification also returning model eval details

    sample_model = {
        "model_name": "Triage_1",
        "f1_score": 0.82,
        "precision": 0.84,
        "recall": 0.80,
        "conf_mat": {
            "true_positive": 120,
            "true_negative": 95,
            "false_positive": 18,
            "false_negative": 22
        }
    }
    model = db.add_model_eval(
        model_name=sample_model["model_name"],
        f1_score=sample_model["f1_score"],
        precision=sample_model["precision"],
        recall=sample_model["recall"],
        conf_mat=json.dumps(sample_model["conf_mat"])
    )

    ## Some logic between two models and then return the results below replacing demo values

    return {
        "model_id": model["model_id"],
        "ats_category": 2,
        "confidence_score": 0.85,
        "severity_flags": True,
        "matched_categories": {
            "severe_bleeding": 2
        },
        "flags": {
            "severe_bleeding": [
                "bleeding heavily"
            ]
        }
    }

@app.post("/cases", response_model=CaseFullOut)
def create_case_endpoint(case: CaseCreate, user=Depends(role_required("Clinician"))):
    try:
        soap_text = soap_summary(case.case_details)
        classification_res = classification_algo(case.case_details)
        severity_info = classification_res["severity_flags"]

        new_case = db.add_case(
            user_id=case.user_id,
            case_details=case.case_details,
            severity_flagged=severity_info
        )
        case_id = new_case["case_id"]
        db.update_soap_summary(case_id, soap_text) #might be replace with anonymise()??

        db.add_classification_model(
            case_id=case_id,
            model_id=classification_res["model_id"],
            ats_classification=classification_res["ats_category"],
            confidence_score=classification_res["confidence_score"]
        )

        severity_flags_reason = None
        if severity_info:
            for label, ats in classification_res["matched_categories"].items():
                severity_flags_reason = ", ".join(classification_res["flags"].get(label, []))
                db.add_severity_flag(case_id, ats, severity_flags_reason)

        return {
            "case_id": case_id,
            "severity_flagged": new_case["severity_flagged"],
            "soap_summary": soap_text,
            "ats_classification": classification_res["ats_category"],
            "confidence_score": classification_res["confidence_score"],
            "flagged_keywords":  severity_flags_reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")

@app.get("/cases/{case_id}")
def get_case(case_id: int):
    """
    Fetch a case by ID with SOAP summary, classification, and severity flags.
    """
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Optional: check if user has permission to view the case
    '''if user["role"] != "Admin" and user["id"] != case["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")'''

    return case

@app.get("/models/{model_name}")
def get_model_metrics(model_name: str):
    """
    Fetch evaluation metrics for a model by name.
    """
    try:
        metrics = db.get_model_metrics_by_name(model_name)
        if not metrics:
            raise HTTPException(status_code=404, detail="Model not found")
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model metrics: {str(e)}")

@app.get("/health")
def health():
    """
    Health check endpoint.
    Returns simple status indicating system is running.
    """
    return {"status": "ok", "message": "System is running smoothly"}
