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
BRIEF_PLACEHOLDER = "Generating brief summary..."

def anonymise_case_for_researcher(case: dict) -> dict:
    anonymised_case = case.copy()

    if anonymised_case.get("case_dialogue"):
        anon_result = deidentify_dialogue(anonymised_case["case_dialogue"])
        anonymised_case["case_dialogue"] = anon_result["deidentified_text"]

    # Hide direct identifiers completely
    anonymised_case["patient_name"] = "[REDACTED]"
    anonymised_case["medicare_number"] = "[REDACTED]"

    return anonymised_case

def generate_and_store_summary(case_id: int, anon_dialogue: str) -> None:
    """
    Runs after the response is sent.
    Generates the SOAP summary and overwrites the placeholder in the DB.
    """
    try:
        soap_object = generate_soap_summary(anon_dialogue)
        db.upsert_clinical_summary(
            case_id=case_id,
            soap_summary=soap_object["soap_markdown"],
            brief_summary=soap_object["brief_summary"],
        )
    except Exception as e:
        # Replace with proper logger later
        print(f"Failed to generate SOAP summary for case {case_id}: {e}")

@router.post("/triage", response_model=CaseFullOut)
@router.post("/cases", response_model=CaseFullOut)
def create_case_endpoint(
    case: CaseCreate,
    background_tasks: BackgroundTasks,
    fast_response: bool = Query(default=True),
    generate_summary: bool = Query(default=True),
    user=Depends(role_required("clinician")),
):
    try:
        if db.has_open_case_for_medicare(case.medicare_number):
            raise HTTPException(status_code=409, detail="An open case already exists for this Medicare number")

        # non-llm service
        classification_res = classify_triage(case.case_dialogue)

        # precise anon
        anon_result = deidentify_dialogue(case.case_dialogue)
        anon_dialogue = anon_result["deidentified_text"]

        is_high_severity = classification_res["is_high_severity"]
        severity_flag_notes = classification_res["severity_flag_notes"]
        final_ats = classification_res["ats_category"]
        final_source = classification_res["decision_source"].strip().lower()

        new_case = db.add_case(
            user_id=user["id"],
            patient_name=case.patient_name,
            medicare_number=case.medicare_number,
            case_dialogue=case.case_dialogue,
            severity_flagged=is_high_severity,
            ats_category=final_ats,
            ats_source=final_source,
            age=case.age,
            gender=case.gender,
        )
        case_id = new_case["case_id"]

        db.add_model_prediction(
            case_id=case_id,
            pred_ats=classification_res["model_ats_category"],
            pred_confidence=classification_res["model_confidence"],
            model_used=CLASSIFICATION_MODEL,
        )

        if is_high_severity:
            db.add_severity_flag(
                case_id=case_id,
                flag_ats=classification_res["ats_category"],
                flag_notes=severity_flag_notes,
            )

        if not generate_summary:
            soap_summary_for_response = "No summary generated"
            brief_summary_for_response = "No summary generated"
            # db.upsert_clinical_summary(
            #     case_id=case_id,
            #     soap_summary=soap_summary_for_response,
            #     brief_summary=brief_summary_for_response,
            # )
        elif fast_response:
            # Store placeholder immediately so GET /cases/{id} can show it
            db.upsert_clinical_summary(
                case_id=case_id,
                soap_summary=SOAP_PLACEHOLDER,
                brief_summary=BRIEF_PLACEHOLDER,
            )

            # Run summary generation after response is sent
            background_tasks.add_task(
                generate_and_store_summary,
                case_id,
                anon_dialogue,
            )

            soap_summary_for_response = SOAP_PLACEHOLDER
            brief_summary_for_response = SOAP_PLACEHOLDER
        else:
            soap_object = generate_soap_summary(anon_dialogue)

            db.upsert_clinical_summary(
                case_id=case_id,
                soap_summary=soap_object["soap_markdown"],
                brief_summary=soap_object["brief_summary"],
            )

            soap_summary_for_response = soap_object["soap_markdown"]
            brief_summary_for_response = soap_object["brief_summary"]

        return {
            "case_id": case_id,
            "patient_name": new_case["patient_name"],
            "medicare_number": new_case["medicare_number"],
            "case_dialogue": new_case["case_dialogue"],
            "severity_flagged": new_case["severity_flagged"],
            "created_at": new_case["created_at"],
            "resolved_at": new_case["resolved_at"],
            "ats_category": new_case["ats_category"],
            "ats_source": new_case["ats_source"],
            "override_ats": new_case["override_ats"],
            "override_reason": new_case["override_reason"],
            "age": new_case["age"],
            "gender": new_case["gender"],
            "pred_ats": classification_res["model_ats_category"],
            "pred_confidence": classification_res["model_confidence"],
            "model_used": CLASSIFICATION_MODEL,
            "flag_ats": classification_res["ats_category"] if is_high_severity else None,
            "flag_notes": severity_flag_notes if is_high_severity else None,
            "soap_summary": soap_summary_for_response,
            "brief_summary": brief_summary_for_response,
        }

    except Exception as e:
        error_text = str(e)
        raise HTTPException(status_code=500, detail=f"Failed to create case: {error_text}")

@router.get("/cases")
@router.get("/triage")
def get_cases(resolved: bool = Query(default=False), user=Depends(get_current_user)):
    cases = db.get_resolved_cases() if resolved else db.get_open_cases()

    if user["role"] == "researcher":
        cases = [anonymise_case_for_researcher(case) for case in cases]

    return cases

@router.get("/cases/{case_id}")
@router.get("/triage/{case_id}")
def get_case(case_id: int, user=Depends(get_current_user)):

    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if user["role"] == "researcher":
        case = anonymise_case_for_researcher(case)

    return case

@router.patch("/cases/{case_id}/resolve")
@router.patch("/triage/{case_id}/resolve")
def resolve_case_endpoint(case_id: int, user=Depends(role_required("clinician"))):
    resolved_case = db.resolve_case(case_id)
    if not resolved_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return resolved_case

@router.patch("/cases/{case_id}/reopen")
@router.patch("/triage/{case_id}/reopen")
def reopen_case_endpoint(case_id: int, user=Depends(role_required("clinician"))):
    reopened_case = db.reopen_case(case_id)
    if not reopened_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return reopened_case

@router.patch("/cases/{case_id}/ats")
@router.patch("/triage/{case_id}/ats")
def override_ats_classification_endpoint(
    case_id: int,
    payload: ATSOverrideRequest,
    user=Depends(role_required("clinician")),
):
    #if user["role"] not in {"admin", "clinician"}:
    #    raise HTTPException(status_code=403, detail="Only Admin or Clinician can override ATS classification")

    updated = db.override_ats_classification(
        case_id=case_id,
        override_ats=payload.override_ats,
        override_reason=payload.override_reason,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "case_id": updated["case_id"],
        "ats_category": updated["ats_category"],
        "ats_source": updated["ats_source"],
        "override_ats": updated["override_ats"],
        "override_reason": updated["override_reason"],
        "message": "ATS classification overridden successfully",
    }

@router.post("/cases/{case_id}/summary")
@router.post("/triage/{case_id}/summary")
def generate_case_summary_endpoint(
    case_id: int,
    background_tasks: BackgroundTasks,
    fast_response: bool = Query(default=False),
    user=Depends(role_required("clinician")),
):
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not case.get("case_dialogue"):
        raise HTTPException(status_code=400, detail="Case dialogue not found")

    try:
        anon_result = deidentify_dialogue(case["case_dialogue"])
        anon_dialogue = anon_result["deidentified_text"]

        if fast_response:
            db.upsert_clinical_summary(
                case_id=case_id,
                soap_summary=SOAP_PLACEHOLDER,
                brief_summary=BRIEF_PLACEHOLDER,
            )

            background_tasks.add_task(
                generate_and_store_summary,
                case_id,
                anon_dialogue,
            )

            return {
                "case_id": case_id,
                "soap_summary": SOAP_PLACEHOLDER,
                "brief_summary": BRIEF_PLACEHOLDER,
                "message": "Clinical summary generation started",
            }

        soap_object = generate_soap_summary(anon_dialogue)

        saved_summary = db.upsert_clinical_summary(
            case_id=case_id,
            soap_summary=soap_object["soap_markdown"],
            brief_summary=soap_object["brief_summary"],
        )

        return {
            "case_id": case_id,
            "soap_summary": saved_summary["soap_summary"],
            "brief_summary": saved_summary["brief_summary"],
            "message": "Clinical summary generated successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
