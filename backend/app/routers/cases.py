from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.core.security import get_current_user
from app.schemas.case import CaseCreate, CaseFullOut
from app.services.case_processing import classification_algo, soap_summary

router = APIRouter()


@router.post("/triage", response_model=CaseFullOut)
def create_case_endpoint(case: CaseCreate, user=Depends(get_current_user)):
    try:
        soap_text = soap_summary(case.case_details)
        classification_res = classification_algo(case.case_details)
        severity_info = classification_res["severity_flags"]

        new_case = db.add_case(
            user_id=user["id"],
            case_details=case.case_details,
            severity_flagged=severity_info["is_high_severity"],
        )
        case_id = new_case["case_id"]
        db.update_soap_summary(case_id, soap_text)

        db.add_classification_model(
            case_id=case_id,
            model_name=classification_res["model_name"],
            ats_classification=classification_res["ats_category"],
            confidence_score=classification_res["confidence_score"],
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
            "flagged_keywords": severity_flags_reason,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")

@router.get("/cases")
def get_open_cases(user=Depends(get_current_user)):
    return db.get_open_cases()

@router.get("/cases/resolved")
def get_resolved_cases(user=Depends(get_current_user)):
    return db.get_resolved_cases()

@router.get("/cases/all")
def get_all_cases(user=Depends(get_current_user)):
    return db.get_all_cases()

@router.get("/cases/{case_id}")
def get_case(case_id: int, user=Depends(get_current_user)):
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/cases/{case_id}/resolve")
def resolve_case_endpoint(case_id: int, user=Depends(get_current_user)):
    resolved_case = db.resolve_case(case_id)
    if not resolved_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return resolved_case

@router.patch("/cases/{case_id}/reopen")
def reopen_case_endpoint(case_id: int, user=Depends(get_current_user)):
    reopened_case = db.reopen_case(case_id)
    if not reopened_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return reopened_case
