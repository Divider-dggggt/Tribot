from __future__ import annotations

import json
from pathlib import Path

from handbook_rag_function_project.pipeline import llm_rag_predict


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / 'configs' / 'app_config.yaml'
    scenarios_path = base_dir / 'handbook_rag_function_project' / 'scenarios.json'

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
