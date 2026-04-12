from pydantic import BaseModel, Field, field_validator
from datetime import datetime


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
        if not value.isdigit() or len(value) != 11:
            raise ValueError("Medicare number must be exactly 11 digits")
        return value

class CaseFullOut(BaseModel):
    case_id: int
    name: str
    medicare_number: str
    severity_flagged: bool
    soap_summary: str
    soap_note: str
    ats_classification: int
    confidence_score: float
    flagged_keywords: str | None
    clinician_override_at: datetime | None = None
    resolved_at: datetime | None = None
    decision_source: str
    rule_based_ats_category: int | None = None
    model_ats_category: int

class ATSOverrideRequest(BaseModel):
    ats_classification: int

    @field_validator("ats_classification")
    @classmethod
    def validate_ats_classification(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("ATS classification must be between 1 and 5")
        return value