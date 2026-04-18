from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.triage_classifier.RAG.handbook_rag_function_project.pipeline import llm_rag_predict


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / 'configs' / 'app_config.yaml'

    scenarios_candidates = [
        base_dir.parent / 'sample_data' / 'scenarios.json',
        base_dir / 'handbook_rag_function_project' / 'scenarios.json',
    ]
    scenarios_path = next((p for p in scenarios_candidates if p.exists()), None)
    if scenarios_path is None:
        raise FileNotFoundError(
            f"Cannot find scenarios.json in: {[str(p) for p in scenarios_candidates]}"
        )

    scenarios = json.loads(scenarios_path.read_text(encoding='utf-8'))
    sample = scenarios[0]

    query_txt = sample['dialogue_text']
    result = llm_rag_predict(query_txt, str(config_path))

    print('scenario_number:', sample.get('scenario_number'))
    print('scenario_summary_header:', sample.get('scenario_summary_header'))
    print('ground_truth_ats_category:', sample.get('ats_category'))
    print('prediction:', json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
