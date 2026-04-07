from fastapi import APIRouter, Depends, HTTPException, Query

from app import db
from app.core.security import get_current_user
from app.schemas.case import CaseCreate, CaseFullOut, ATSOverrideRequest
from app.services.case_processing import classification_algo, soap_summary
from app.services.anonymisation import deidentify_dialogue
from psycopg2.errors import UniqueViolation

router = APIRouter()


@router.post("/triage", response_model=CaseFullOut)
def create_case_endpoint(case: CaseCreate, user=Depends(get_current_user)):
    try:
        classification_res = classification_algo(case.case_details) #non-llm service

        anon_result = deidentify_dialogue(case.case_details) #precise anon
        anon_dialogue = anon_result["deidentified_text"]

        soap_text = soap_summary(anon_dialogue) #SOAP generation with precise anon
        print(anon_dialogue)

        severity_info = classification_res["severity_flags"]

        new_case = db.add_case(
            user_id=user["id"],
            name=case.name,
            medicare_number=case.medicare_number,
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

        if severity_info["is_high_severity"]:
            all_reasons = []

            for label, ats in severity_info["matched_categories"].items():
                reasons = severity_info["flags"].get(label, [])
                reason_text = ", ".join(reasons) if reasons else label

                db.add_severity_flag(case_id, ats, reason_text)
                all_reasons.extend(reasons)

            severity_flags_reason = ", ".join(sorted(set(all_reasons))) if all_reasons else None
        else:
            severity_flags_reason = None

        return {
            "case_id": case_id,
            "name": new_case["name"],
            "medicare_number": new_case["medicare_number"],
            "severity_flagged": new_case["severity_flagged"],
            "soap_summary": soap_text,
            "ats_classification": classification_res["ats_category"],
            "confidence_score": classification_res["confidence_score"],
            "flagged_keywords": severity_flags_reason,
            "clinician_override_at": None,
            "resolved_at": new_case["resolved_at"],
        }

    except Exception as e:
        error_text = str(e)

        if "medicare_number" in error_text:
            raise HTTPException(status_code=409, detail="Medicare number already exists")

        raise HTTPException(status_code=500, detail=f"Failed to create case: {error_text}")

@router.get("/cases")
def get_cases(resolved: bool = Query(default=False), user=Depends(get_current_user)):
    if resolved:
        return db.get_resolved_cases()
    return db.get_open_cases()


#@router.get("/cases")
#def get_open_cases(user=Depends(get_current_user)):
#    return db.get_open_cases()

#@router.get("/cases/resolved")
#def get_resolved_cases(user=Depends(get_current_user)):
#    return db.get_resolved_cases()

#@router.get("/cases/all")
#def get_all_cases(user=Depends(get_current_user)):
#    return db.get_all_cases()

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

@router.patch("/cases/{case_id}/ats")
def override_ats_classification_endpoint(
    case_id: int,
    payload: ATSOverrideRequest,
    user=Depends(get_current_user),
):
    updated = db.override_ats_classification(
        case_id=case_id,
        ats_classification=payload.ats_classification,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Classification record not found for case")

    return {
        "case_id": updated["case_id"],
        "ats_classification": updated["ats_classification"],
        "clinician_override_at": updated["clinician_override_at"],
        "message": "ATS classification overridden successfully",
    }
