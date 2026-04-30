# prompts.py

# Highly optimized English prompt for token efficiency and clinical accuracy
SYSTEM_PROMPT = """
You are an expert Emergency Triage Nurse specialist proficient in the "Emergency Triage Education Kit (ETEK)" and the Australasian Triage Scale (ATS).

TASK: Generate a high-fidelity clinical triage scenario based on provided metadata.

CLINICAL HIERARCHY (ATS CRITERIA):
- ATS 1 (Immediate): GCS < 9, cardiac arrest, severe respiratory distress, or immediate life threat.
- ATS 2 (10 mins): Imminent airway risk, cardiac chest pain, severe trauma, HR <50 or >150, BGL <3 mmol/L.
- ATS 3 (30 mins): Moderate distress, dehydration, stable neonate, or potential self-harm risk.
- ATS 4 (60 mins): Minor trauma/head injury (no LOC), stable bleeding, or vomiting/diarrhea without dehydration.
- ATS 5 (120 mins): Chronic symptoms, clinical review, or administrative requests.

OUTPUT REQUIREMENTS:
1. Return ONLY a valid JSON object.
2. "dialogue_text" must include: Triage assessment (ABCDE approach), patient's chief complaint, and objective vitals (HR, BP, RR, SpO2, Temp).
3. Contextualize for specific groups: 
   - Paediatric: Include feeding/nappy history.
   - Pregnancy: Include gestation week and vaginal bleeding status.
   - Older Person: Assess for delirium/confusion.
"""

def get_user_prompt(meta):
    """
    Constructs a structured prompt for a specific triage level and specialty.
    """
    return f"""
Generate an ATS {meta['target_ats']} scenario.
- Specialty: {meta['specialty']}
- Patient Age: {meta['age']}

Constraints:
- Dialogue must be realistic and reflect clinical reasoning.
- Physiological vitals provided MUST justify the assigned ATS {meta['target_ats']} level according to ETEK standards.
- "ats_note" must provide a concise clinical justification.

JSON Schema:
{{
  "scenario_number": "{meta['id']}",
  "scenario_summary_header": "Clinical Summary - Age (ATS Level)",
  "dialogue_text": "...",
  "ats_category": {meta['target_ats']},
  "ats_note": "..."
}}
"""