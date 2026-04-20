
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

PATIENT_SPK = {"Patient", "Parent", "Child", "Relative"}
TRIVIAL_PATIENT = {
    "okay", "okay.", "thank you", "thank you.", "okay, thank you", "okay, thank you.",
    "oh dear.", "oh god.", "oh… okay.", "perfect.", "yes.", "no.", "yes", "no"
}
SYMPTOM_HINTS = [
    "pain", "fever", "warm", "hot", "sleepy", "drowsy", "floppy", "wheezy", "breathe", "breathing",
    "vomit", "vomiting", "diarrhoea", "cough", "runny nose", "rash", "seizure", "fit", "swallowed",
    "short of breath", "bleeding", "spotting", "dizzy", "faint", "fainted", "headache", "vision",
    "swelling", "red", "sore", "itchy", "weak", "confused", "urine", "pee", "blood", "nausea", "tight"
]
HISTORY_HINTS = [
    "diagnosed", "history", "vaccinated", "full-term", "nicu", "pregnant", "pregnancy", "depression",
    "meds", "medication", "previous", "past", "allerg", "diabetic", "diabetes", "copd", "asthma",
    "heart failure", "warfarin", "apixaban", "smoke", "hospitalisations", "breastfeeding", "osteoporosis",
    "enlarged prostate", "support at home"
]
NEGATION_HINTS = ["no ", "none", "not ", "never", "nope", "nil "]


def parse_turns(dialogue: str) -> List[Tuple[str, str]]:
    blocks = [b.strip() for b in dialogue.split("\n\n") if b.strip()]
    turns: List[Tuple[str, str]] = []
    for block in blocks:
        m = re.match(r"^(Nurse|Patient|Parent|Child|Relative):\s*(.*)", block, flags=re.S)
        if m:
            turns.append((m.group(1), m.group(2).strip()))
        else:
            turns.append(("Stage", block.strip()))
    return turns


def sent_split(text: str) -> List[str]:
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[\.\?\!])\s+", text)
    return [p.strip(" -") for p in parts if p.strip(" -")]


def is_trivial_patient_sentence(s: str) -> bool:
    low = s.lower().strip()
    if low in TRIVIAL_PATIENT:
        return True
    if s.strip().endswith("?"):
        return True
    if re.match(r"^(is|will|am|do|did|does|can|could)\b", low):
        return True
    return False


def classify_patient_sentence(s: str) -> str | None:
    low = s.lower()
    if is_trivial_patient_sentence(s):
        return None
    if low.startswith(tuple(NEGATION_HINTS)) or re.search(r"\bno\b", low):
        return "negative"
    if any(h in low for h in HISTORY_HINTS):
        return "history"
    if any(h in low for h in SYMPTOM_HINTS):
        return "symptom"
    return "symptom"


def choose_chief_complaint(turns: List[Tuple[str, str]], header: str) -> str:
    fallback = None
    for speaker, text in turns:
        if speaker in {"Patient", "Parent", "Relative"}:
            for sentence in sent_split(text):
                if is_trivial_patient_sentence(sentence):
                    continue
                low = sentence.lower()
                fallback = fallback or sentence
                if any(h in low for h in SYMPTOM_HINTS) and not re.match(r"^(yes|no)\b", low):
                    return sentence
    return fallback or header.split(" - ")[0].strip()


def extract_age_history(header: str) -> str:
    parts = header.split(" - ")
    return parts[-1].strip() if len(parts) > 1 else ""


def dedupe(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        value = re.sub(r"\s+", " ", str(value)).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def criticality_for_text(text: str, section: str) -> str:
    low = text.lower()
    high_kw = [
        "suicid", "anaphyl", "airway", "stridor", "drooling", "ectopic", "pre-eclamps",
        "chest pain", "acs", "dka", "sepsis", "gi bleed", "haematemesis", "spo2", "pregnan",
        "bleeding", "seizure", "confused", "delirium", "hip fracture", "fracture", "breathing",
        "short of breath", "hypoxia", "overdose", "oxycodone", "thunderclap", "headache"
    ]
    med_kw = [
        "vomit", "diarrhoea", "dehydrat", "wound", "laceration", "appendic", "cellulitis",
        "retention", "syncope", "renal colic", "vertigo", "mastitis", "anaemia", "coin",
        "foreign body", "asthma", "copd", "heart failure"
    ]
    if any(k in low for k in high_kw):
        return "high"
    if any(k in low for k in med_kw):
        return "medium"
    return "low"


def must_include(text: str, section: str, idx: int) -> bool:
    crit = criticality_for_text(text, section)
    low = text.lower()
    if section in {"assessment", "plan", "objective"}:
        return True
    if idx <= 3 or crit in {"high", "medium"}:
        return True
    if low.startswith(("no ", "not ", "never")) and any(k in low for k in ["pain", "vomit", "vomiting", "rash", "bleeding", "breathing", "chest", "drooling", "fever"]):
        return True
    return False


def extract_from_scenario(scenario: Dict) -> Dict:
    turns = parse_turns(scenario["dialogue_text"])
    subjective = {
        "chief_complaint": choose_chief_complaint(turns, scenario["scenario_summary_header"]),
        "history_of_present_illness": [],
        "associated_symptoms": [],
        "negatives": [],
        "relevant_history": [],
    }
    age_history = extract_age_history(scenario["scenario_summary_header"])
    if age_history:
        subjective["relevant_history"].append(age_history)

    objective = {"vitals": {}, "exam_findings": [], "observed_general_state": []}
    assessment = [scenario["ats_note"].rstrip(".")]
    plan: List[str] = []

    for speaker, text in turns:
        if speaker in PATIENT_SPK:
            for sentence in sent_split(text):
                cls = classify_patient_sentence(sentence)
                if not cls:
                    continue
                if cls == "negative":
                    subjective["negatives"].append(sentence)
                elif cls == "history":
                    subjective["relevant_history"].append(sentence)
                else:
                    low = sentence.lower()
                    if any(k in low for k in ["cough", "runny nose", "nausea", "vomit", "diarrhoea", "rash", "swelling", "short of breath", "chest pain", "sweat", "light-headed", "blurry vision", "chills", "drooling", "wheeze", "fever", "tummy hurts", "throat feels tight", "blue", "spotting", "hoarse voice"]):
                        subjective["associated_symptoms"].append(sentence)
                    else:
                        subjective["history_of_present_illness"].append(sentence)
        elif speaker == "Nurse":
            nurse_text = text.replace("\n", " ")
            for sentence in sent_split(nurse_text):
                low = sentence.lower()
                if "?" in sentence:
                    continue
                if re.search(r"\b(temp(?:erature)?|oxygen|spo2|blood pressure|bp|heart rate|pulse|rr|respiratory rate|bgl)\b", low):
                    objective["exam_findings"].append(sentence)
                elif any(k in low for k in ["breathing looks", "air entry", "tender", "swelling", "warm,", "warm ", "red streaking", "facial swelling", "hoarse voice", "mouth is a bit dry", "mouth dry", "cap refill", "capillary refill", "dry mucus membranes", "using his tummy muscles", "equal, no stridor", "no stridor or wheeze", "circulation is good", "fingers warm", "good colour", "shortened and turned outward", "looks infected", "colour is okay", "stable for now", "alert, pale", "warm, swollen, red", "distended", "deformity", "fluid retention"]):
                    objective["exam_findings"].append(sentence)
                elif any(k in low for k in ["looks stable", "looks normal", "showing signs of", "physically stable", "he's sleepy", "you look a bit breathless", "he's definitely working harder", "she's showing signs"]):
                    objective["observed_general_state"].append(sentence)
                if any(k in low for k in ["possible", "likely", "concerning for", "showing signs of", "sounds like", "you may have", "you may be", "could indicate", "this is likely", "active anaphylaxis", "moderate dehydration", "suspected", "needs urgent", "needs timely", "needs proper fluids", "need to rule out", "risk of your breathing slowing down", "not immediately life threatening"]):
                    assessment.append(sentence)
                if any(k in low for k in ["we'll", "we will", "i'm going to", "we need to", "take you", "get you", "straight through", "no waiting", "acute area", "acute care", "resus", "x-ray", "blood tests", "bloods", "urine", "ultrasound", "monitor", "seen soon", "doctor will", "mental health team", "obstetrics", "pain relief", "antibiotics", "steroids", "nebulisers", "catheter", "iv antibiotics", "fluids", "private and safe", "safe room", "ecg straight away"]):
                    plan.append(sentence)

    exam_blob = " ".join(objective["exam_findings"])
    temp = re.findall(r"(?:temp(?:erature)?(?: is| still up -)?|temp )\s*(\d{2}\.?\d?)", exam_blob, flags=re.I)
    if not temp:
        temp = re.findall(r"(\d{2}\.\d)\b", exam_blob)
    spo2 = re.findall(r"(?:oxygen (?:is|level is)|spo2(?:\)| is)?)(?:\s*at)?\s*(\d{2,3})%?", exam_blob, flags=re.I)
    bp = re.findall(r"(?:bp|blood pressure)(?: is| of)?(?: elevated at)?\s*(\d{2,3}/\d{2,3})", exam_blob, flags=re.I)
    if temp:
        objective["vitals"]["temperature_c"] = temp[0]
    if spo2:
        objective["vitals"]["spo2_percent"] = spo2[0]
    if bp:
        objective["vitals"]["bp_mmHg"] = bp[0]
    if any(x in exam_blob.lower() for x in ["pulse is a bit fast", "heart rate is a bit fast", "heart rate's fast", "pulse fast", "heart rate fast", "pulse is elevated"]):
        objective["vitals"]["heart_rate"] = "tachycardic / fast"

    if scenario["ats_category"] in [1, 2] and not any(re.search(r"acute|straight through|resus|urgent|no waiting", p, re.I) for p in plan):
        plan.append("Urgent review and transfer to an acute treatment area.")

    for key in list(subjective):
        if isinstance(subjective[key], list):
            subjective[key] = dedupe(subjective[key])
    objective["exam_findings"] = dedupe(objective["exam_findings"])
    objective["observed_general_state"] = dedupe(objective["observed_general_state"])
    assessment = dedupe(assessment)
    plan = dedupe(plan)

    return {"subjective": subjective, "objective": objective, "assessment": assessment, "plan": plan}


def build_facts(record: Dict) -> List[Dict]:
    facts: List[Dict] = []
    soap = record["gold_soap"]
    sid = record["scenario_number"]
    counter = 1

    def add(section: str, typ: str, text: str, polarity: str = "positive", optional: bool = False) -> None:
        nonlocal counter
        text = str(text).strip()
        if not text:
            return
        facts.append({
            "fact_id": f"{sid}_F{counter:02d}",
            "section_gold": section,
            "type": typ,
            "content": text,
            "evidence_span": text,
            "criticality": criticality_for_text(text, section),
            "polarity": polarity,
            "must_include": False if optional else must_include(text, section, counter),
        })
        counter += 1

    add("subjective", "chief_complaint", soap["subjective"]["chief_complaint"])
    for x in soap["subjective"]["history_of_present_illness"]:
        add("subjective", "history_of_present_illness", x)
    for x in soap["subjective"]["associated_symptoms"]:
        add("subjective", "associated_symptom", x)
    for x in soap["subjective"]["negatives"]:
        add("subjective", "negative", x, polarity="negative")
    for x in soap["subjective"]["relevant_history"]:
        add("subjective", "relevant_history", x, optional=(criticality_for_text(x, "subjective") == "low"))
    for k, v in soap["objective"]["vitals"].items():
        add("objective", "vital_sign", f"{k}: {v}")
    for x in soap["objective"]["exam_findings"]:
        add("objective", "exam_finding", x)
    for x in soap["objective"]["observed_general_state"]:
        add("objective", "observed_state", x)
    for x in soap["assessment"]:
        add("assessment", "assessment", x)
    for x in soap["plan"]:
        add("plan", "plan", x)

    return facts


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild benchmark gold annotations from scenario JSON.")
    default_scenarios = Path(__file__).resolve().parents[3] / "sample_data" / "scenarios.json"
    parser.add_argument(
        "--scenarios",
        default=str(default_scenarios),
        help=f"Path to scenarios.json (default: {default_scenarios})",
    )
    parser.add_argument("--out_json", required=True, help="Path to output gold_annotations.json")
    args = parser.parse_args()

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    out = []
    for scenario in scenarios:
        record = {
            "scenario_number": scenario["scenario_number"],
            "summary_header": scenario["scenario_summary_header"],
            "ats_category": scenario["ats_category"],
            "ats_note": scenario["ats_note"],
            "gold_soap": extract_from_scenario(scenario),
        }
        record["facts"] = build_facts(record)
        out.append(record)

    Path(args.out_json).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(out)} records to {args.out_json}")


if __name__ == "__main__":
    main()
