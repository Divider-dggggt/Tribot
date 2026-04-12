from pathlib import Path
from app.services.soap_generator import init_soap_generator, generate_soap

_INITIALIZED = False


def _format_soap_to_markdown(soap: dict) -> str:
    """Convert structured SOAP JSON into a readable markdown string."""

    def format_list(items):
        return "\n".join(f"- {item}" for item in items) if items else "- None"

    subjective = soap.get("subjective", {})
    objective = soap.get("objective", {})

    markdown = f"""
## Subjective
**Chief Complaint:** {subjective.get("chief_complaint", "") or "None"}

**History of Present Illness:**
{format_list(subjective.get("history_of_present_illness", []))}

**Associated Symptoms:**
{format_list(subjective.get("associated_symptoms", []))}

**Negatives:**
{format_list(subjective.get("negatives", []))}

**Relevant History:**
{format_list(subjective.get("relevant_history", []))}

---

## Objective
**Vitals:**
{format_list([f"{k}: {v}" for k, v in objective.get("vitals", {}).items()])}

**Exam Findings:**
{format_list(objective.get("exam_findings", []))}

**Observed General State:**
{format_list(objective.get("observed_general_state", []))}

---

## Assessment
{format_list(soap.get("assessment", []))}

---

## Plan
{format_list(soap.get("plan", []))}
""".strip()

    return markdown


def generate_soap_summary(dialogue_text: str) -> dict:
    global _INITIALIZED

    if not _INITIALIZED:
        script_dir = Path(__file__).resolve().parent
        config_path = script_dir / "config.yaml"
        init_soap_generator(config_path=str(config_path))
        _INITIALIZED = True

    result = generate_soap({
        "dialogue_text": dialogue_text
    })

    soap_markdown = _format_soap_to_markdown(result["soap"])
    brief_summary = result.get("brief_summary", "")

    return {
        "soap_markdown": soap_markdown,
        "brief_summary": brief_summary,
    }