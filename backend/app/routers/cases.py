from fastapi import APIRouter, Depends, HTTPException, Query

from app import db
from app.core.security import get_current_user
from app.schemas.case import CaseCreate, CaseFullOut, ATSOverrideRequest
from app.services.anonymisation import deidentify_dialogue
from app.services.soap_generator.summariser_service import generate_soap_summary
from app.services.triage_classifier.triage_classifier_service import classify_triage
from psycopg2.errors import UniqueViolation

router = APIRouter()
CLASSIFICATION_MODEL = 'setfit'

@router.post("/triage", response_model=CaseFullOut)
def create_case_endpoint(case: CaseCreate, user=Depends(get_current_user)):
    try:
        # non-llm service
        classification_res = classify_triage(case.case_details) 

        # precise anon
        anon_result = deidentify_dialogue(case.case_details) 
        anon_dialogue = anon_result["deidentified_text"]

        # SOAP generation with precise anon
        soap_object = generate_soap_summary(anon_dialogue)
        # return {
        #     "soap_markdown": soap_markdown,
        #     "brief_summary": brief_summary,
        # }

        # severity_info = classification_res["severity_flags"]
        is_high_severity = classification_res["is_high_severity"]
        # flags_detected = classification_res["flags_detected"]
        severity_flag_notes = classification_res["severity_flag_notes"]

        new_case = db.add_case(
            user_id=user["id"],
            name=case.name,
            medicare_number=case.medicare_number,
            case_details=case.case_details,
            severity_flagged=is_high_severity,
        )
        case_id = new_case["case_id"]
        db.update_soap_summary(case_id, soap_object["brief_summary"])

        db.add_classification_model(
            case_id=case_id,
            # model_name=classification_res["decision_source"],
            model_name=CLASSIFICATION_MODEL,
            ats_classification=classification_res["ats_category"],
            confidence_score=classification_res["model_confidence"],
        )

        if is_high_severity:
            # all_reasons = []

            # for label, ats in severity_info["matched_categories"].items():
            #     reasons = severity_info["flags"].get(label, [])
            #     reason_text = ", ".join(reasons) if reasons else label

            #     db.add_severity_flag(case_id, ats, reason_text)
            #     all_reasons.extend(reasons)
            db.add_severity_flag(case_id, classification_res["ats_category"], severity_flag_notes)

            # severity_flags_reason = ", ".join(sorted(set(all_reasons))) if all_reasons else None

            severity_flags_reason = severity_flag_notes
        else:
            severity_flags_reason = None

        return {
            "case_id": case_id,
            "name": new_case["name"],
            "medicare_number": new_case["medicare_number"],
            "severity_flagged": new_case["severity_flagged"],
            "soap_summary": soap_object["soap_markdown"],
            "soap_note": soap_object["brief_summary"],
            "ats_classification": classification_res["ats_category"],
            "confidence_score": classification_res["model_confidence"],
            "flagged_keywords": severity_flag_notes,
            "clinician_override_at": None,
            "resolved_at": new_case["resolved_at"],

            "decision_source": classification_res["decision_source"],
            "rule_based_ats_category": classification_res["rule_based_ats_category"],
            "model_ats_category": classification_res["model_ats_category"],
        }

    except Exception as e:
        error_text = str(e)

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
    if user["role"] not in {"Admin", "Clinician"}:
        raise HTTPException(status_code=403, detail="Only Admin or Clinician can override ATS classification")

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
