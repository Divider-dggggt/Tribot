import re
import sys
import json
from pathlib import Path
from collections import defaultdict


NEGATION_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bwithout\b",
    r"\bnegative for\b",
    r"\bfree of\b",
    r"\bnil\b",
]

NEGATION_RE = re.compile("|".join(NEGATION_PATTERNS), re.IGNORECASE)


def normalize_text(text: str) -> str:
    return (
        text.replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
        .replace("—", "-")
    )


def is_negated(text: str, match_start: int, window_chars: int = 40) -> bool:
    start = max(0, match_start - window_chars)
    prefix = text[start:match_start].lower()
    return bool(NEGATION_RE.search(prefix))


def find_matches(text: str, patterns: list[str]) -> list[str]:
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if not is_negated(text, match.start()):
                matches.append(match.group(0))
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for m in matches:
        key = m.lower()
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique


# -------------------------
# 1. Base presentations
# -------------------------
BASE_PRESENTATIONS = {
    "cardiac_chest_pain": {
        "base_score": 4,
        "patterns": [
            r"\bcentral chest pain\b",
            r"\bcrushing chest pain\b",
            r"\bheavy chest pain\b",
            r"\bchest pain\b",
            r"\bpain in (the )?chest\b",
            r"\bchest tightness\b",
        ],
    },

    "shortness_of_breath": {
        "base_score": 4,
        "patterns": [
            r"\bshortness of breath\b",
            r"\bdifficulty breathing\b",
            r"\btrouble breathing\b",
            r"\bbreathless\b",
            r"\bbreathlessness\b",
            r"\bwheezy\b",
            r"\bwheezing\b",
        ],
    },

    "stroke_like_symptoms": {
        "base_score": 5,
        "patterns": [
            r"\bsuspected stroke\b",
            r"\bstroke symptoms\b",
            r"\bface droop\b",
            r"\bfacial droop\b",
            r"\bslurred speech\b",
            r"\bone-sided weakness\b",
            r"\bunilateral weakness\b",
            r"\bnew focal neurological deficit\b",
        ],
    },

    "seizure": {
        "base_score": 3,
        "patterns": [
            r"\bseizure\b",
            r"\bseizures\b",
            r"\bconvulsion\b",
            r"\bconvulsions\b",
            r"\bfit\b",
            r"\bfitting\b",
            r"\btonic[- ]clonic\b",
        ],
    },

    "severe_bleeding": {
        "base_score": 5,
        "patterns": [
            r"\bsevere bleeding\b",
            r"\bheavy bleeding\b",
            r"\bprofuse bleeding\b",
            r"\bmassive bleeding\b",
            r"\bbleeding heavily\b",
            r"\bhaemorrhage\b",
            r"\bhemorrhage\b",
        ],
    },

    "allergic_reaction": {
        "base_score": 4,
        "patterns": [
            r"\banaphylaxis\b",
            r"\banaphylactic reaction\b",
            r"\bsevere allergic reaction\b",
            r"\ballergic reaction\b",
        ],
    },

    "syncope_loss_of_consciousness": {
        "base_score": 3,
        "patterns": [
            r"\bsyncope\b",
            r"\bpassed out\b",
            r"\bloss of consciousness\b",
            r"\blost consciousness\b",
            r"\bunconscious\b",
            r"\bblacked out\b",
            r"\bblack out\b",
        ],
    },

    "infection_sepsis": {
        "base_score": 3,
        "patterns": [
            r"\bsepsis\b",
            r"\bsuspected sepsis\b",
            r"\bfebrile neutropenia\b",
            r"\bfever\b",
            r"\bfevers\b",
            r"\binfection\b",
            r"\bfever with lethargy\b",
        ],
    },

    "moderate_bleeding": {
        "base_score": 3,
        "patterns": [
            r"\bbleeding\b",
            r"\bbleed(?:ing)? from\b",
            r"\bongoing bleeding\b",
        ],
    },

    "non_cardiac_chest_pain_possible": {
        "base_score": 3,
        "patterns": [
            r"\bsharp chest pain\b",
            r"\bpleuritic chest pain\b",
            r"\bchest discomfort\b",
        ],
    },
}


# -------------------------
# 2. Upward modifiers
# -------------------------
UPWARD_MODIFIERS = {
    "cardiac_features": {
        "score": 2,
        "patterns": [
            r"\bradiat(?:es|ing)? to (the )?(arm|jaw|shoulder)\b",
            r"\barm heaviness\b",
            r"\bthroat tight(ness)?\b",
            r"\bpressure\b",
            r"\bheavy feeling\b",
            r"\bclammy\b",
            r"\bdiaphoretic\b",
            r"\bsweaty\b",
        ],
        "applies_to": {"chest_pain"},
    },
    "respiratory_distress": {
        "score": 2,
        "patterns": [
            r"\bsevere shortness of breath\b",
            r"\bextreme shortness of breath\b",
            r"\bsevere respiratory distress\b",
            r"\bmarked respiratory distress\b",
            r"\busing accessory muscles\b",
            r"\btracheal tug\b",
            r"\bunable to speak\b",
            r"\bspeaking in short sentences\b",
            r"\bpulling in under (his|her|their) ribs\b",
        ],
        "applies_to": {"shortness_of_breath", "allergic_reaction", "infection_sepsis"},
    },
    "reduced_consciousness": {
        "score": 2,
        "patterns": [
            r"\bdrowsy\b",
            r"\breduced consciousness\b",
            r"\bconfused\b",
            r"\bunresponsive\b",
            r"\brousable to voice\b",
            r"\bnot orient(?:ed|ated)\b",
            r"\bdecreased responsiveness\b",
            r"\bgcs\b",
        ],
        "applies_to": {"seizure", "stroke_like", "syncope", "infection_sepsis"},
    },
    "haemodynamic_concern": {
        "score": 2,
        "patterns": [
            r"\bpale and clammy\b",
            r"\bpoor perfusion\b",
            r"\bmottled\b",
            r"\bhypotens(?:ion|ive)\b",
            r"\btachycard(?:ia|ic)\b",
            r"\bshock\b",
            r"\bcollaps(?:e|ed)\b",
        ],
        "applies_to": {"chest_pain", "bleeding", "infection_sepsis", "syncope", "allergic_reaction"},
    },
    "high_risk_history": {
        "score": 1,
        "patterns": [
            r"\bdiabet(?:es|ic)\b",
            r"\bhypertension\b",
            r"\bhigh blood pressure\b",
            r"\bhigh cholesterol\b",
            r"\bcardiac history\b",
            r"\barrhythmia\b",
            r"\bcoronary artery disease\b",
            r"\bmi\b",
            r"\bstent\b",
            r"\bheart attack\b",
            r"\basthma\b",
            r"\bcopd\b",
            r"\bimmunosupp(?:ressed|ression)\b",
            r"\bchemotherapy\b",
            r"\bmethotrexate\b",
            r"\bprednisone\b",
            r"\banticoagulant\b",
            r"\bwarfarin\b",
            r"\bapixaban\b",
            r"\brivaroxaban\b",
        ],
        "applies_to": {
            "chest_pain", "shortness_of_breath", "syncope",
            "infection_sepsis", "stroke_like", "bleeding"
        },
    },
    "age_extremes": {
        "score": 1,
        "patterns": [
            r"\b(\d{1,2})\s*(year old|yo)\b",
            r"\binfant\b",
            r"\btoddler\b",
            r"\belderly\b",
            r"\bolder\b",
        ],
        "applies_to": {
            "chest_pain", "shortness_of_breath", "seizure",
            "syncope", "infection_sepsis", "stroke_like"
        },
    },
    "injury_or_head_strike": {
        "score": 1,
        "patterns": [
            r"\bhit (his|her|their) head\b",
            r"\bhead injury\b",
            r"\bhead strike\b",
            r"\bfell\b",
            r"\btrauma\b",
        ],
        "applies_to": {"seizure", "syncope"},
    },
    "sepsis_red_flags": {
        "score": 2,
        "patterns": [
            r"\bletharg(?:ic|y)\b",
            r"\bfebrile neutropenia\b",
            r"\bfever with lethargy\b",
            r"\breduced oral intake\b",
            r"\bdecreased urine output\b",
            r"\boff food and fluids\b",
        ],
        "applies_to": {"infection_sepsis"},
    },
}


# -------------------------
# 3. Light downward modifiers
# -------------------------
DOWNWARD_MODIFIERS = {
    "returned_to_baseline": {
        "score": -1,
        "patterns": [
            r"\bnow alert\b",
            r"\bback to baseline\b",
            r"\bfully recovered\b",
            r"\bpain has gone\b",
            r"\bsymptoms resolved\b",
        ],
        "applies_to": {"seizure", "syncope", "chest_pain"},
    },
    "possible_benign_context": {
        "score": -1,
        "patterns": [
            r"\bmusculoskeletal\b",
            r"\bpanic attack\b",
            r"\banxiety\b",
            r"\bpreviously well\b",
            r"\bfit and well\b",
        ],
        "applies_to": {"chest_pain", "shortness_of_breath", "syncope"},
    },
}


# -------------------------
# 4. Hard overrides
# -------------------------
HARD_OVERRIDES = [
    {
        "name": "ats_1_airway_breathing",
        "ats": 1,
        "patterns": [
            r"\brespiratory arrest\b",
            r"\bextreme respiratory distress\b",
            r"\bairway compromise\b",
            r"\bsevere stridor\b",
            r"\bdrooling with distress\b",
        ],
    },
    {
        "name": "ats_1_seizure",
        "ats": 1,
        "patterns": [
            r"\bongoing seizure\b",
            r"\bprolonged seizure\b",
            r"\bstatus epilepticus\b",
        ],
    },
    {
        "name": "ats_1_circulation",
        "ats": 1,
        "patterns": [
            r"\bcardiac arrest\b",
            r"\bunresponsive\b",
            r"\bbp < ?80\b",
            r"\bmassive haemorrhage\b",
            r"\bmassive hemorrhage\b",
        ],
    },
    {
        "name": "ats_2_stroke",
        "ats": 2,
        "patterns": [
            r"\bsuspected stroke\b",
            r"\bacute stroke\b",
            r"\bface droop\b",
            r"\bslurred speech\b",
            r"\bone-sided weakness\b",
        ],
    },
]


def detect_presentations(text: str) -> dict:
    results = {}

    for name, config in BASE_PRESENTATIONS.items():
        matches = find_matches(text, config["patterns"])
        if matches:
            results[name] = {
                "score": config["base_score"],
                "base_matches": matches,
                "upward_modifiers": {},
                "downward_modifiers": {},
            }

    return results


def apply_modifiers(text: str, presentations: dict) -> None:
    for mod_name, config in UPWARD_MODIFIERS.items():
        mod_matches = find_matches(text, config["patterns"])
        if not mod_matches:
            continue

        for pres_name in presentations:
            if pres_name in config["applies_to"]:
                presentations[pres_name]["score"] += config["score"]
                presentations[pres_name]["upward_modifiers"][mod_name] = mod_matches

    for mod_name, config in DOWNWARD_MODIFIERS.items():
        mod_matches = find_matches(text, config["patterns"])
        if not mod_matches:
            continue

        for pres_name in presentations:
            if pres_name in config["applies_to"]:
                # keep reductions conservative
                presentations[pres_name]["score"] += config["score"]
                presentations[pres_name]["downward_modifiers"][mod_name] = mod_matches


def check_hard_overrides(text: str) -> list[dict]:
    triggered = []
    for override in HARD_OVERRIDES:
        matches = find_matches(text, override["patterns"])
        if matches:
            triggered.append({
                "name": override["name"],
                "ats": override["ats"],
                "matches": matches,
            })
    return triggered


def score_to_ats(score: int) -> int | None:
    """
    Suggested starting point for weighted severity rules.

    Score meaning:
    6+  = critical / near-ATS 1 territory
    5   = strong ATS 2 presentation
    4   = ATS 2 unless modifiers clearly soften it
    3   = ATS 3 baseline
    2   = ATS 4 baseline
    1   = ATS 5 baseline
    """

    if score >= 6:
        return 1
    if score >= 4:
        return 2
    if score == 3:
        return 3
    if score == 2:
        return 4
    if score == 1:
        return 5
    return None


def build_severity_flag_notes(
    final_ats: int | None,
    presentations: dict,
    overrides: list[dict],
) -> str:
    parts = []

    # ATS at the front
    if final_ats is not None:
        parts.append(f"ATS {final_ats}")

    # Overrides (clean wording)
    if overrides:
        override_names = [
            o["name"].replace("_", " ") for o in overrides
        ]
        parts.append(f"override: {', '.join(override_names)}")

    for pres_name, data in presentations.items():
        readable_name = pres_name.replace("_", " ")

        base_matches = data.get("base_matches", [])

        upward_values = []
        for matches in data.get("upward_modifiers", {}).values():
            upward_values.extend(matches)

        downward_values = []
        for matches in data.get("downward_modifiers", {}).values():
            downward_values.extend(matches)

        # de-duplicate
        upward_values = list(dict.fromkeys(upward_values))
        downward_values = list(dict.fromkeys(downward_values))

        section_parts = []

        if base_matches:
            section_parts.append(", ".join(base_matches))

        if upward_values:
            section_parts.append(f"with {', '.join(upward_values)}")

        if downward_values:
            section_parts.append(f"(reduced by {', '.join(downward_values)})")

        if section_parts:
            parts.append(f"{readable_name}: {' '.join(section_parts)}")
        else:
            parts.append(readable_name)

    if not parts:
        return "No severity flags detected."

    return " | ".join(parts)


def flag_high_severity(text: str) -> dict:
    text = normalize_text(text)

    presentations = detect_presentations(text)
    apply_modifiers(text, presentations)
    overrides = check_hard_overrides(text)

    override_ats = min((o["ats"] for o in overrides), default=None)

    scored_presentations = {}
    recommended_from_scores = None

    for name, data in presentations.items():
        score = max(0, data["score"])
        ats = score_to_ats(score)

        scored_presentations[name] = {
            "score": score,
            "provisional_ats": ats,
            "base_matches": data["base_matches"],
            "upward_modifiers": data["upward_modifiers"],
            "downward_modifiers": data["downward_modifiers"],
        }

        if ats is not None:
            if recommended_from_scores is None:
                recommended_from_scores = ats
            else:
                recommended_from_scores = min(recommended_from_scores, ats)

    final_ats = recommended_from_scores
    if override_ats is not None:
        final_ats = override_ats if final_ats is None else min(final_ats, override_ats)
    
    severity_flag_notes = build_severity_flag_notes(
        final_ats=final_ats,
        presentations=scored_presentations,
        overrides=overrides,
    )

    return {
        "is_high_severity": bool(presentations or overrides),
        "recommended_ats_category": final_ats,
        "severity_flag_notes": severity_flag_notes,
        "override_applied": bool(overrides),
        "overrides": overrides,
        "presentations": scored_presentations,
    }


def read_input_text() -> str:
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        return input_path.read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise ValueError(
        "No input provided. Use either:\n"
        "  python severity_flagging.py path/to/file.txt\n"
        "or:\n"
        "  python severity_flagging.py < path/to/file.txt"
    )


def main():
    try:
        input_text = read_input_text()
        if not input_text.strip():
            raise ValueError("Input text is empty.")

        result = flag_high_severity(input_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()