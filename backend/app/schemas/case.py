from pydantic import BaseModel, field_validator
from datetime import datetime


class CaseCreate(BaseModel):
    patient_name: str
    medicare_number: str
    case_dialogue: str
    age: int | None = None
    gender: str | None = None

    @field_validator("patient_name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Patient name cannot be empty")
        return value

    @field_validator("medicare_number")
    @classmethod
    def validate_medicare_number(cls, value: str):
        value = value.strip()
        if not value.isdigit() or len(value) != 11:
            raise ValueError("Medicare number must be exactly 11 digits")
        return value

    @field_validator("case_dialogue")
    @classmethod
    def validate_case_dialogue(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Case dialogue cannot be empty")
        return value

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int | None):
        if value is not None and (value < 0 or value > 150):
            raise ValueError("Age must be between 0 and 150")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None):
        if value is None:
            return value
        value = value.strip().lower()
        if value not in {"male", "female", "other"}:
            raise ValueError("Gender must be one of: male, female, other")
        return value

class CaseOut(BaseModel):
    case_id: int
    patient_name: str
    medicare_number: str
    severity_flagged: bool
    created_at: datetime
    resolved_at: datetime | None = None
    ats_category: int
    ats_source: str
    override_ats: int | None = None
    override_reason: str | None = None
    age: int | None = None
    gender: str | None = None

class CaseFullOut(BaseModel):
    case_id: int
    patient_name: str
    medicare_number: str
    case_dialogue: str

    severity_flagged: bool
    created_at: datetime
    resolved_at: datetime | None = None

    ats_category: int
    ats_source: str
    override_ats: int | None = None
    override_reason: str | None = None

    age: int | None = None
    gender: str | None = None

    pred_ats: int | None = None
    pred_confidence: float | None = None
    model_used: str | None = None

    flag_ats: int | None = None
    flag_notes: str | None = None

    soap_summary: str | None = None
    brief_summary: str | None = None

    @field_validator("ats_source")
    @classmethod
    def validate_ats_source(cls, value: str):
        value = value.strip().lower()
        if value not in {"model", "rule", "override"}:
            raise ValueError("ATS source must be one of: model, rule, override")
        return value
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None):
        if value is None:
            return value
        value = value.strip().lower()
        if value not in {"male", "female", "other"}:
            raise ValueError("Gender must be one of: male, female, other")
        return value

class ATSOverrideRequest(BaseModel):
    override_ats: int
    override_reason: str | None = None

    @field_validator("override_ats")
    @classmethod
    def validate_ats_classification(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("Override ATS must be between 1 and 5")
        return value