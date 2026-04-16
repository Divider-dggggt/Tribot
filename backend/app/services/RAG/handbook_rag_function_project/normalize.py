from __future__ import annotations

import re
from typing import List


def handbook_fit(query_txt: str, chunks: List[dict]) -> dict:
    q = query_txt.strip()
    low = q.lower()
    special = []
    if any(x in low for x in ['pregnan', 'gestation', 'weeks pregnant', 'fetal', 'foetal', 'vaginal bleeding']):
        special.append('pregnancy')
    if any(x in low for x in ['child', 'toddler', 'parent', 'infant', 'baby', 'months old', 'years old']):
        special.append('paediatrics')
    if any(x in low for x in ['suicid', 'self-harm', 'psychosis', 'agitated', 'behavioural']):
        special.append('mental_health')
    if re.search(r'\b(7\d|8\d|9\d)\s*/\s*(4\d|5\d)', low) or 'hypotension' in low:
        most_urgent = 'circulation compromise / possible shock'
    elif 'gcs' in low or 'confus' in low or 'seizure' in low or 'unresponsive' in low:
        most_urgent = 'disability / altered consciousness'
    elif any(x in low for x in ['cannot breathe', 'can\'t breathe', 'short of breath', 'wheeze', 'respiratory distress', 'spo2', 'oxygen saturation']):
        most_urgent = 'breathing compromise'
    elif any(x in low for x in ['chest pain', 'crushing pain', 'left arm', 'jaw pain']):
        most_urgent = 'possible time-critical chest pain'
    else:
        most_urgent = 'general presenting problem'

    evidence_summary = ' | '.join(c['citation'] for c in chunks[:3])
    handbook_text = ' '.join(c['content'][:300] for c in chunks[:3])
    augmented = f"Query: {q}\nMost urgent feature: {most_urgent}\nSpecial populations: {', '.join(special) if special else 'none'}\nRetrieved handbook evidence: {handbook_text}"
    return {
        'original_query': q,
        'most_urgent_feature': most_urgent,
        'special_populations': special,
        'evidence_summary': evidence_summary,
        'augmented_text': augmented,
        'retrieved_chunks': chunks,
    }
