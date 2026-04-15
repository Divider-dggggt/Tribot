from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app import db
from app.core.security import get_current_user, role_required
from app.schemas.case import CaseCreate, CaseFullOut, ATSOverrideRequest
from app.services.anonymisation import deidentify_dialogue
from app.services.soap_generator.summariser_service import generate_soap_summary
from app.services.triage_classifier.triage_classifier_service import classify_triage

router = APIRouter()
CLASSIFICATION_MODEL = 'deberta'
SOAP_PLACEHOLDER = "Generating clinical summary..."

def anonymise_case_for_researcher(case: dict) -> dict:
    anonymised_case = case.copy()

    if anonymised_case.get("case_details"):
        anon_result = deidentify_dialogue(anonymised_case["case_details"])
        anonymised_case["case_details"] = anon_result["deidentified_text"]

    # Hide direct identifiers completely
    anonymised_case["name"] = "[REDACTED]"
    anonymised_case["medicare_number"] = "[REDACTED]"

    return anonymised_case

def generate_and_store_summary(case_id: int, anon_dialogue: str) -> None:
    """
    Runs after the response is sent.
    Generates the SOAP summary and overwrites the placeholder in the DB.
    """
    try:
        soap_object = generate_soap_summary(anon_dialogue)
        db.update_soap_summary(case_id, soap_object["soap_markdown"])
    except Exception as e:
        # Replace with proper logger later
        print(f"Failed to generate SOAP summary for case {case_id}: {e}")

@router.post("/triage", response_model=CaseFullOut)
@router.post("/cases", response_model=CaseFullOut)
def create_case_endpoint(
    case: CaseCreate,
    background_tasks: BackgroundTasks,
    fast_response: bool = Query(default=True),
    user=Depends(role_required("Clinician")),
):
    try:
        # non-llm service
        classification_res = classify_triage(case.case_details)

        # precise anon
        anon_result = deidentify_dialogue(case.case_details)
        anon_dialogue = anon_result["deidentified_text"]

        is_high_severity = classification_res["is_high_severity"]
        severity_flag_notes = classification_res["severity_flag_notes"]

        new_case = db.add_case(
            user_id=user["id"],
            name=case.name,
            medicare_number=case.medicare_number,
            case_details=case.case_details,
            severity_flagged=is_high_severity,
        )
        case_id = new_case["case_id"]

        db.add_classification_model(
            case_id=case_id,
            model_name=CLASSIFICATION_MODEL,
            ats_classification=classification_res["ats_category"],
            confidence_score=classification_res["model_confidence"],
        )

        if is_high_severity:
            db.add_severity_flag(
                case_id,
                classification_res["ats_category"],
                severity_flag_notes,
            )

        if fast_response:
            # Store placeholder immediately so GET /cases/{id} can show it
            db.update_soap_summary(case_id, SOAP_PLACEHOLDER)

            # Run summary generation after response is sent
            background_tasks.add_task(
                generate_and_store_summary,
                case_id,
                anon_dialogue,
            )

            soap_summary_for_response = SOAP_PLACEHOLDER
            soap_note_for_response = SOAP_PLACEHOLDER

        else:
            soap_object = generate_soap_summary(anon_dialogue)

            db.update_soap_summary(case_id, soap_object["soap_markdown"])

            soap_summary_for_response = soap_object["soap_markdown"]
            soap_note_for_response = soap_object["brief_summary"]

        return {
            "case_id": case_id,
            "name": new_case["name"],
            "medicare_number": new_case["medicare_number"],
            "severity_flagged": new_case["severity_flagged"],
            "soap_summary": soap_summary_for_response,
            "soap_note": soap_note_for_response,
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
@router.get("/triage")
def get_cases(resolved: bool = Query(default=False), user=Depends(get_current_user)):

    cases = db.get_all_cases() if resolved else db.get_open_cases()

    if user["role"] == "Researcher":
        cases = [anonymise_case_for_researcher(case) for case in cases]

    return  cases

@router.get("/cases/{case_id}")
@router.get("/triage/{case_id}")
def get_case(case_id: int, user=Depends(get_current_user)):

    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if user["role"] == "Researcher":
        case = anonymise_case_for_researcher(case)

    return case

@router.patch("/cases/{case_id}/resolve")
@router.patch("/triage/{case_id}/resolve")
def resolve_case_endpoint(case_id: int, user=Depends(role_required("Clinician"))):
    resolved_case = db.resolve_case(case_id)
    if not resolved_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return resolved_case

@router.patch("/cases/{case_id}/reopen")
@router.patch("/triage/{case_id}/reopen")
def reopen_case_endpoint(case_id: int, user=Depends(role_required("Clinician"))):
    reopened_case = db.reopen_case(case_id)
    if not reopened_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return reopened_case

@router.patch("/cases/{case_id}/ats")
@router.patch("/triage/{case_id}/ats")
def override_ats_classification_endpoint(
        case_id: int,
        payload: ATSOverrideRequest,
        user=Depends(role_required("Clinician")),
):
    #if user["role"] not in {"Admin", "Clinician"}:
    #    raise HTTPException(status_code=403, detail="Only Admin or Clinician can override ATS classification")

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
