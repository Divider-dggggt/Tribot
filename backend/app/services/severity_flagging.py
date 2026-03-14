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

HIGH_SEVERITY_PATTERNS = {
    "chest_pain": [
        r"\bchest pain\b",
        r"\bpain in (the )?chest\b",
    ],
    "severe_shortness_of_breath": [
        r"\bsevere shortness of breath\b",
        r"\bextreme shortness of breath\b",
        r"\bmarked shortness of breath\b",
        r"\bshortness of breath\b",
        r"\bdifficulty breathing\b",
        r"\btrouble breathing\b",
        r"\bsevere breathlessness\b",
        r"\bextreme breathlessness\b",
        r"\bmarked breathlessness\b",
    ],
    "stroke_symptoms": [
        r"\bstroke symptoms\b",
        r"\bsymptoms of stroke\b",
        r"\bshows symptoms of stroke\b",
        r"\bshowing symptoms of stroke\b",
        r"\bsuspected stroke\b",
        r"\bpossible stroke\b",
    ],
    "seizures": [
        r"\bseizure\b",
        r"\bseizures\b",
        r"\bconvulsion\b",
        r"\bconvulsions\b",
        r"\bfitting\b",
        r"\bfit\b",
    ],
    "severe_bleeding": [
        r"\bsevere bleeding\b",
        r"\bheavy bleeding\b",
        r"\bprofuse bleeding\b",
        r"\bmassive bleeding\b",
        r"\bbleeding heavily\b",
    ],
    "anaphylaxis": [
        r"\banaphylaxis\b",
        r"\banaphylactic reaction\b",
        r"\bsevere allergic reaction\b",
    ],
    "loss_of_consciousness": [
        r"\bloss of consciousness\b",
        r"\blost consciousness\b",
        r"\bunconscious\b",
        r"\bpassed out\b",
        r"\bblacked out\b",
        r"\bblack out\b",
        r"\bsyncope\b",
    ],
}

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


def flag_high_severity(text: str) -> dict:
    text = normalize_text(text)
    flags = defaultdict(list)

    for label, pattern_list in HIGH_SEVERITY_PATTERNS.items():
        for pattern in pattern_list:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if not is_negated(text, match.start()):
                    flags[label].append(match.group(0))

    deduped_flags = {}
    for label, matches in flags.items():
        seen = set()
        unique_matches = []
        for m in matches:
            key = m.lower()
            if key not in seen:
                seen.add(key)
                unique_matches.append(m)
        deduped_flags[label] = unique_matches

    return {
        "is_high_severity": len(deduped_flags) > 0,
        "flags": deduped_flags,
    }


def read_input_text() -> str:
    """
    Read from a file path argument if provided, otherwise from stdin.
    """
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