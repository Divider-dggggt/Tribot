from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(text: str) -> str:
    text = str(text or "")
    text = text.lower()
    text = text.replace("↓spo₂", "low spo2")
    text = text.replace("spo₂", "spo2")
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"[^a-z0-9/%\.\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> List[str]:
    text = str(text or "").replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return []
    parts = re.split(r"(?<=[\.\?\!])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def flatten_iterable_text(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                out.append(value.strip())
        else:
            text = str(value).strip()
            if text:
                out.append(text)
    return out


@dataclass
class MatchResult:
    score: float
    index: int
    text: str


class TextMatcher:
    """Hybrid matcher using TF-IDF char ngrams + RapidFuzz token-set ratio."""

    def __init__(self, corpus: Sequence[str]) -> None:
        self.corpus = [normalize_text(x) for x in corpus]

    def best_match(self, query: str, candidates: Sequence[str]) -> MatchResult:
        if not candidates:
            return MatchResult(score=0.0, index=-1, text="")
        norm_candidates = [normalize_text(x) for x in candidates]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        matrix = vectorizer.fit_transform(norm_candidates + [normalize_text(query)])
        sims = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        best_idx = int(sims.argmax()) if len(sims) else -1
        best_cos = float(sims[best_idx]) if best_idx >= 0 else 0.0

        rf_scores = [
            fuzz.token_set_ratio(normalize_text(query), cand) / 100.0
            for cand in norm_candidates
        ]
        best_rf_idx = int(max(range(len(rf_scores)), key=lambda i: rf_scores[i]))
        best_rf = float(rf_scores[best_rf_idx])

        if best_rf >= best_cos:
            return MatchResult(score=best_rf, index=best_rf_idx, text=candidates[best_rf_idx])
        return MatchResult(score=best_cos, index=best_idx, text=candidates[best_idx])

    def pairwise_best_scores(self, queries: Sequence[str], candidates: Sequence[str]) -> List[MatchResult]:
        return [self.best_match(q, candidates) for q in queries]
