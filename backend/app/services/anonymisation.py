import re

DEIDENTIFICATION_PATTERNS = {
    "dob": [
        r"\bDOB\s*[:\-]?\s*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
        r"\bdate of birth\s*[:\-]?\s*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
    ],
    "date": [
        r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
        r"\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b",
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2},?\s+\d{4}\b",
    ],
    "time": [
        r"\b\d{1,2}:\d{2}\s?(?:am|pm|AM|PM)?\b",
        r"\b\d{1,2}\s?(?:am|pm|AM|PM)\b",
    ],
    "email": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    ],
    "phone": [
        r"\b(?:\+?61\s?|0)\d(?:[\s\-]?\d){8,9}\b",   # catches 0412 345 678, 04xx xxx xxx, +61 ...
    ],
    "id_number": [
        r"\b\d{8,12}\b",
    ],
    "address": [
        r"\b\d{1,5}\s+[A-Z][a-zA-Z0-9'\-]*(?:\s+[A-Z][a-zA-Z0-9'\-]*)*\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl)\b",
    ],
    "age": [
        r"\b\d{1,3}\s*(?:years old|year old|yo|y/o)\b",
        r"\baged\s+\d{1,3}\b",
        r"\b\d{1,3}-year-old\b",
    ],
    "patient_name_intro": [
        r"\bThis is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"\b(?:His|Her|Their) name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"\bI(?:'m| am) here with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    ],
    "self_intro": [
        r"\bI(?:'m| am)\s+([A-Z][a-z]+)\b",
        r"\bMy name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
    ],
    "person_name": [
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",
    ],
}

PLACEHOLDER_MAP = {
    "dob": "[DOB]",
    "date": "[DATE]",
    "time": "[TIME]",
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "id_number": "[ID_NUMBER]",
    "address": "[ADDRESS]",
    "age": "[AGE]",
    "patient_name_intro": "[PATIENT_NAME]",
    "self_intro": "[NAME]",
    "person_name": "[NAME]",
}

SPEAKER_LABEL_PATTERN = r"^\s*(Nurse|Doctor|Dr|Parent|Patient|Carer|Clinician|Registrar)\s*:"
NAME_EXCLUSIONS = {
    "Nurse", "Doctor", "Parent", "Patient", "Carer", "Clinician",
    "Registrar", "Emergency", "Hospital"
}

CONFIG = {
    "mask_age": True,
    "mask_date": True,
    "mask_time": True,
    "mask_names": True,
}

def deidentify_dialogue(dialogue: str) -> dict:
    """
    Baseline rule-based de-identification for clinical dialogue.

    Args:
        dialogue (str): Raw dialogue text

    Returns:
        dict: {
            "deidentified_text": str,
            "items_detected": list[dict],
            "deidentification_applied": bool
        }
    """
    if not isinstance(dialogue, str):
        raise TypeError("dialogue must be a string")

    deidentified_text = dialogue
    items_detected = []

    def add_detection(entity_type: str, matched_text: str, replacement: str):
        items_detected.append({
            "type": entity_type,
            "matched_text": matched_text,
            "replacement": replacement
        })

    def replace_with_placeholder(text: str, pattern: str, entity_type: str, replacement: str, flags=0):
        def repl(match):
            original = match.group(0)
            add_detection(entity_type, original, replacement)
            return replacement
        return re.sub(pattern, repl, text, flags=flags)

    def replace_intro_name(text: str, pattern: str, entity_type: str, replacement: str, flags=0):
        def repl(match):
            original = match.group(0)
            name_part = match.group(1)
            updated = original.replace(name_part, replacement, 1)
            add_detection(entity_type, original, updated)
            return updated
        return re.sub(pattern, repl, text, flags=flags)

    # Speaker labels like "Nurse:" should remain unchanged.
    # Do not try to replace names in speaker labels unless they actually exist.
    # If later your transcripts contain "Nurse Ben:", you can add a separate pattern.

    # DOB first so internal dates don't get separately counted
    for pattern in DEIDENTIFICATION_PATTERNS["dob"]:
        deidentified_text = replace_with_placeholder(
            deidentified_text, pattern, "dob", "[DOB]", flags=re.IGNORECASE
        )

    if CONFIG["mask_date"]:
        for pattern in DEIDENTIFICATION_PATTERNS["date"]:
            deidentified_text = replace_with_placeholder(
                deidentified_text, pattern, "date", "[DATE]", flags=re.IGNORECASE
            )

    if CONFIG["mask_time"]:
        for pattern in DEIDENTIFICATION_PATTERNS["time"]:
            deidentified_text = replace_with_placeholder(
                deidentified_text, pattern, "time", "[TIME]"
            )

    for pattern in DEIDENTIFICATION_PATTERNS["email"]:
        deidentified_text = replace_with_placeholder(
            deidentified_text, pattern, "email", "[EMAIL]"
        )

    for pattern in DEIDENTIFICATION_PATTERNS["phone"]:
        deidentified_text = replace_with_placeholder(
            deidentified_text, pattern, "phone", "[PHONE]"
        )

    for pattern in DEIDENTIFICATION_PATTERNS["address"]:
        deidentified_text = replace_with_placeholder(
            deidentified_text, pattern, "address", "[ADDRESS]"
        )

    for pattern in DEIDENTIFICATION_PATTERNS["id_number"]:
        deidentified_text = replace_with_placeholder(
            deidentified_text, pattern, "id_number", "[ID_NUMBER]"
        )

    if CONFIG["mask_age"]:
        for pattern in DEIDENTIFICATION_PATTERNS["age"]:
            deidentified_text = replace_with_placeholder(
                deidentified_text, pattern, "age", "[AGE]", flags=re.IGNORECASE
            )

    if CONFIG["mask_names"]:
        for pattern in DEIDENTIFICATION_PATTERNS["patient_name_intro"]:
            deidentified_text = replace_intro_name(
                deidentified_text, pattern, "patient_name_intro", "[PATIENT_NAME]"
            )

        for pattern in DEIDENTIFICATION_PATTERNS["self_intro"]:
            deidentified_text = replace_intro_name(
                deidentified_text, pattern, "self_intro", "[NAME]"
            )

        # Generic full-name masking last
        def replace_person_name(match):
            original = match.group(0)
            parts = original.split()

            if any(part in NAME_EXCLUSIONS for part in parts):
                return original

            add_detection("person_name", original, "[NAME]")
            return "[NAME]"

        deidentified_text = re.sub(
            DEIDENTIFICATION_PATTERNS["person_name"][0],
            replace_person_name,
            deidentified_text
        )

    # Cleanup
    deidentified_text = re.sub(r"\[DATE\]\.", "[DATE].", deidentified_text)
    deidentified_text = re.sub(r"\[(?:NAME|PATIENT_NAME)\]\s+\[(?:NAME|PATIENT_NAME)\]", "[NAME]", deidentified_text)

    return {
        "deidentified_text": deidentified_text,
        "items_detected": items_detected,
        "deidentification_applied": len(items_detected) > 0
    }


if __name__ == "__main__":
    sample_dialogue = """
    Nurse: Hi there, I'm Ben, one of the triage nurses. What's his name?
    Patient: This is Noah. He's 3 years old.
    Nurse: When did this start?
    Patient: Around 2:30 pm on 12/03/2026.
    Patient: My phone number is 0412 345 678 and email is maryjones@email.com.
    Patient: We live at 14 George Street.
    Patient: His date of birth is 03/08/2022.
    Patient: Yes, the 3rd of August.
    """

    result = deidentify_dialogue(sample_dialogue)

    print("De-identified text:\n")
    print(result["deidentified_text"])

    print("\nItems detected:\n")
    for item in result["items_detected"]:
        print(item)