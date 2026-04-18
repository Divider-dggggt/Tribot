from __future__ import annotations

from pathlib import Path
import json
import pickle
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .indexing import simple_tokenize


class Retriever:
    def __init__(self, artifacts_dir: str):
        p = Path(artifacts_dir)
        with open(p / 'handbook_chunks.json', 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        with open(p / 'bm25.pkl', 'rb') as f:
            self.bm25 = pickle.load(f)
        self.index = faiss.read_index(str(p / 'faiss.index'))
        with open(p / 'index_meta.json', 'r', encoding='utf-8') as f:
            meta = json.load(f)
        self.embedder = SentenceTransformer(meta['embedding_model_name'])

    def retrieve(self, query: str, bm25_top_k: int = 8, vector_top_k: int = 8, final_top_k: int = 6) -> List[dict]:
        toks = simple_tokenize(query)
        bm25_scores = self.bm25.get_scores(toks)
        bm25_idx = np.argsort(bm25_scores)[::-1][:bm25_top_k]

        q = self.embedder.encode([query], normalize_embeddings=True).astype('float32')
        vec_scores, vec_idx = self.index.search(q, vector_top_k)
        vec_scores = vec_scores[0]
        vec_idx = vec_idx[0]

        fused = {}
        for rank, idx in enumerate(bm25_idx, start=1):
            fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (60 + rank)
        for rank, idx in enumerate(vec_idx, start=1):
            fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (60 + rank)

        top = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:final_top_k]
        out = []
        for idx, score in top:
            row = dict(self.chunks[idx])
            row['retrieval_score'] = float(score)
            out.append(row)
        return out
