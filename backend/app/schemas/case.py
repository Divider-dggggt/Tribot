from pydantic import BaseModel
from datetime import datetime
class CaseCreate(BaseModel):
    case_details: str


class CaseFullOut(BaseModel):
    case_id: int
    severity_flagged: bool
    soap_summary: str
    ats_classification: int
    confidence_score: float
    flagged_keywords: str | None
    resolved_at: datetime | None = None
