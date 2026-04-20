from __future__ import annotations

import json
import pickle
import re
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .text_utils import normalize_text


def _chunk_text(text: str, page_num: int, max_words: int = 220, overlap_words: int = 40) -> List[Dict]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    words = text.split()
    chunks: List[Dict] = []
    start = 0
    chunk_id = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        chunk_text = " ".join(words[start:end]).strip()
        if chunk_text:
            chunks.append({"chunk_id": f"p{page_num:03d}_c{chunk_id:03d}", "page": page_num, "text": chunk_text})
            chunk_id += 1
        if end == len(words):
            break
        start = max(0, end - overlap_words)
    return chunks


def build_handbook_index(pdf_path: str, out_dir: str) -> Dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(pdf_path)
    chunks: List[Dict] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.extend(_chunk_text(text=text, page_num=i))

    texts = [normalize_text(x["text"]) for x in chunks]
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(texts)

    (out / "chunks.json").write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "vectorizer.pkl").open("wb") as f:
        pickle.dump(vectorizer, f)
    with (out / "matrix.pkl").open("wb") as f:
        pickle.dump(matrix, f)

    return {
        "chunks": str(out / "chunks.json"),
        "vectorizer": str(out / "vectorizer.pkl"),
        "matrix": str(out / "matrix.pkl"),
    }


class HandbookIndex:
    def __init__(self, index_dir: str) -> None:
        index_path = Path(index_dir)
        self.chunks = json.loads((index_path / "chunks.json").read_text(encoding="utf-8"))
        with (index_path / "vectorizer.pkl").open("rb") as f:
            self.vectorizer = pickle.load(f)
        with (index_path / "matrix.pkl").open("rb") as f:
            self.matrix = pickle.load(f)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        q = self.vectorizer.transform([normalize_text(query)])
        sims = cosine_similarity(q, self.matrix).flatten()
        order = sims.argsort()[::-1][:top_k]
        results = []
        for idx in order:
            chunk = dict(self.chunks[int(idx)])
            chunk["score"] = float(sims[int(idx)])
            results.append(chunk)
        return results
