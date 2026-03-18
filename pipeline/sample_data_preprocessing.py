import re
import json
import csv
from pathlib import Path
from collections import Counter


SCENARIO_START_RE = re.compile(r'^\s*SCENARIO\s+(\d{4})\s*$', re.MULTILINE)
ATS_LINE_RE = re.compile(r'^\s*ATS Category:\s*(\d)\s*[—–-]\s*(.+?)\s*$', re.IGNORECASE)


def normalize_text(text: str) -> str:
    """
    Normalise common unicode punctuation so parsing is more robust.
    """
    return (
        text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("—", "-")
            .replace("–", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
    )


def split_scenarios(raw_text: str) -> list[str]:
    matches = list(SCENARIO_START_RE.finditer(raw_text))
    if not matches:
        raise ValueError("No scenario headers found. Expected lines like 'SCENARIO 0001'.")

    scenario_blocks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()
        scenario_blocks.append(block)

    return scenario_blocks


def parse_single_scenario(block: str) -> dict:
    lines = [line.rstrip() for line in block.splitlines()]

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        raise ValueError("Encountered an empty scenario block.")

    scenario_match = re.match(r'^\s*SCENARIO\s+(\d{4})\s*$', lines[0])
    if not scenario_match:
        raise ValueError(f"Missing scenario number header in block:\n{block[:300]}")

    scenario_number = scenario_match.group(1)

    ats_idx = None
    ats_category = None
    ats_note = None

    for i, line in enumerate(lines):
        ats_match = ATS_LINE_RE.match(line)
        if ats_match:
            ats_idx = i
            ats_category = int(ats_match.group(1))
            ats_note = ats_match.group(2).strip()
            break

    if ats_idx is None:
        raise ValueError(f"No ATS Category line found for scenario {scenario_number}")

    body_lines = lines[1:ats_idx]

    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    if not body_lines:
        raise ValueError(f"No scenario body found for scenario {scenario_number}")

    scenario_summary_header = body_lines[0].strip()
    dialogue_lines = body_lines[1:]

    while dialogue_lines and not dialogue_lines[0].strip():
        dialogue_lines.pop(0)
    while dialogue_lines and not dialogue_lines[-1].strip():
        dialogue_lines.pop()

    dialogue_text = "\n".join(dialogue_lines).strip()

    return {
        "scenario_number": scenario_number,
        "scenario_summary_header": scenario_summary_header,
        "dialogue_text": dialogue_text,
        "ats_category": ats_category,
        "ats_note": ats_note,
    }


def parse_all_scenarios(raw_text: str) -> list[dict]:
    raw_text = normalize_text(raw_text)
    blocks = split_scenarios(raw_text)
    return [parse_single_scenario(block) for block in blocks]


def save_json(parsed_scenarios: list[dict], output_dir: Path) -> Path:
    json_path = output_dir / "scenarios.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_scenarios, f, indent=2, ensure_ascii=False)
    return json_path


def save_dialogue_txts(parsed_scenarios: list[dict], output_dir: Path) -> Path:
    dialogues_dir = output_dir / "dialogues"
    dialogues_dir.mkdir(parents=True, exist_ok=True)

    for item in parsed_scenarios:
        txt_path = dialogues_dir / f"{item['scenario_number']}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(item["dialogue_text"])

    return dialogues_dir


def save_labels_csv(parsed_scenarios: list[dict], output_dir: Path) -> Path:
    csv_path = output_dir / "labels.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario_number", "ats_category"])
        for item in parsed_scenarios:
            writer.writerow([item["scenario_number"], item["ats_category"]])
    return csv_path


def count_ats_categories(parsed_scenarios: list[dict]) -> dict[int, int]:
    counts = Counter(item["ats_category"] for item in parsed_scenarios)
    return dict(sorted(counts.items()))


def save_category_counts_csv(category_counts: dict[int, int], output_dir: Path) -> Path:
    csv_path = output_dir / "ats_category_counts.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ats_category", "count"])
        for category, count in category_counts.items():
            writer.writerow([category, count])
    return csv_path


def main():
    input_path = Path("sample_data/sample_data_file.txt")
    output_dir = Path("sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError("Could not find sample_data_file.txt in the current directory.")

    raw_text = input_path.read_text(encoding="utf-8")
    parsed_scenarios = parse_all_scenarios(raw_text)

    json_path = save_json(parsed_scenarios, output_dir)
    dialogues_dir = save_dialogue_txts(parsed_scenarios, output_dir)
    labels_csv_path = save_labels_csv(parsed_scenarios, output_dir)

    category_counts = count_ats_categories(parsed_scenarios)
    # counts_csv_path = save_category_counts_csv(category_counts, output_dir)

    print(f"Parsed {len(parsed_scenarios)} scenarios.")
    print(f"Saved JSON: {json_path}")
    print(f"Saved dialogue txt files in: {dialogues_dir}")
    print(f"Saved labels CSV: {labels_csv_path}")
    # print(f"Saved ATS category counts CSV: {counts_csv_path}")
    print("\nATS category counts:")
    for category, count in category_counts.items():
        print(f"ATS {category}: {count}")


if __name__ == "__main__":
    main()