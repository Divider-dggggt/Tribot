from __future__ import annotations

import json
from pathlib import Path
import re
import requests
import yaml
from dotenv import load_dotenv
import os


DEFAULT_ENV_PATH = Path(__file__).resolve().parents[5] / '.env'


def _load_llm_settings(llm_config_yaml: str) -> dict:
    with open(llm_config_yaml, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    llm = cfg['llm']
    base_url = llm['url'].rstrip('/')
    model = llm['model'] if isinstance(llm['model'], str) else next(iter(llm['model'].values()))
    if isinstance(model, list):
        model = model[0]

    # Load a single API key from backend/.env.
    load_dotenv(DEFAULT_ENV_PATH, override=False)
    api_key = os.getenv('LLM_API_KEY', '').strip()
    if not api_key:
        raise ValueError('LLM_API_KEY is empty or missing in backend/.env')

    return {'base_url': base_url, 'api_key': api_key, 'model': model}


def _extract_json(text: str) -> dict:
    m = re.search(r'\{.*\}', text, flags=re.S)
    if not m:
        raise ValueError('No JSON object found in LLM response')
    return json.loads(m.group(0))


def llm_classify_and_explain(query_txt: str, fit: dict, cfg: dict) -> dict:
    llmset = _load_llm_settings(cfg['paths']['llm_config_yaml'])
    chunks = fit['retrieved_chunks'][: cfg['llm'].get('max_context_chunks', 4)]
    evidence = '\n\n'.join([f"[{i+1}] {c['citation']}\n{c['content'][:700]}" for i,c in enumerate(chunks)])
    prompt = f"""
You are an Australian ED triage assistant grounded only in the supplied handbook evidence.
Return JSON only with keys: ats_category, confidence, citation.
- ats_category must be integer 1-5.
- confidence must be a number 0-1 if you can estimate it, otherwise null.
- citation must be a short citation string quoting one relevant handbook location.
Use the handbook's most urgent clinical feature logic.

User query:
{query_txt}

Handbook-fit summary:
Most urgent feature: {fit['most_urgent_feature']}
Special populations: {', '.join(fit['special_populations']) if fit['special_populations'] else 'none'}

Evidence:
{evidence}
""".strip()
    url = llmset['base_url'] + '/chat/completions'
    headers = {'Authorization': f"Bearer {llmset['api_key']}", 'Content-Type': 'application/json'}
    body = {
        'model': llmset['model'],
        'temperature': cfg['llm'].get('temperature', 0.1),
        'messages': [
            {'role': 'system', 'content': 'Return JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
    }
    resp = requests.post(url, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data['choices'][0]['message']['content']
    obj = _extract_json(content)
    return {
        'ats_category': int(obj['ats_category']),
        'confidence': None if obj.get('confidence') is None else float(obj['confidence']),
        'citation': str(obj['citation']),
    }
