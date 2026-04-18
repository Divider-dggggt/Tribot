from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List
import re
import fitz


@dataclass
class Chunk:
    chunk_id: str
    page_start: int
    page_end: int
    chapter: str
    section: str
    chunk_type: str
    content: str
    citation: str


def _guess_chunk_type(text: str) -> str:
    low = text.lower()
    if 'table ' in low or 'ats categories' in low or 'triage categories' in low:
        return 'table'
    if 'case study' in low or 'scenario' in low:
        return 'case_study'
    if any(x in low for x in ['pregnancy', 'paediatric', 'older people', 'psychological distress', 'behavioural disturbance']):
        return 'special_population'
    if any(x in low for x in ['key point', 'when applying the ats', 'take-home messages']):
        return 'rule'
    return 'general_principle'


def parse_pdf_to_chunks(pdf_path: str, chunk_size_chars: int = 1400, chunk_overlap_chars: int = 200) -> List[Chunk]:
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        text = doc[i].get_text("text")
        text = re.sub(r'\s+\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        pages.append((i + 1, text))

    chunks: List[Chunk] = []
    cur_chapter = 'Unknown'
    cur_section = 'General'
    serial = 0

    for page_no, text in pages:
        if not text:
            continue
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for ln in lines[:8]:
            if ln.lower().startswith('chapter '):
                cur_chapter = ln
                break
        for ln in lines[:12]:
            if ln.lower() in {'about this chapter', 'background', 'the ats', 'red flags', 'assessment', 'other considerations', 'take-home messages', 'educator resources', 'references'}:
                cur_section = ln
                break

        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size_chars)
            content = text[start:end].strip()
            if content:
                serial += 1
                ctype = _guess_chunk_type(content)
                citation = f"ETEK p.{page_no} {cur_chapter} / {cur_section}"
                chunks.append(Chunk(
                    chunk_id=f"chunk_{serial:05d}",
                    page_start=page_no,
                    page_end=page_no,
                    chapter=cur_chapter,
                    section=cur_section,
                    chunk_type=ctype,
                    content=content,
                    citation=citation,
                ))
            if end == len(text):
                break
            start = max(start + 1, end - chunk_overlap_chars)

    return chunks


def chunks_to_dicts(chunks: List[Chunk]) -> List[dict]:
    return [asdict(c) for c in chunks]
