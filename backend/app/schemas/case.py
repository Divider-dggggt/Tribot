from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class CaseCreate(BaseModel):
    case_details: str

class CaseCreate(BaseModel):
    name: str
    medicare_number: str
    case_details: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("medicare_number")
    @classmethod
    def validate_medicare_number(cls, value: str):
        value = value.strip()
        if not value.isdigit() or len(value) != 8:
            raise ValueError("Medicare number must be exactly 8 digits")
        return value

class CaseFullOut(BaseModel):
    case_id: int
    name: str
    medicare_number: str
    severity_flagged: bool
    soap_summary: str
    ats_classification: int
    confidence_score: float
    flagged_keywords: str | None
    resolved_at: datetime | None = None

