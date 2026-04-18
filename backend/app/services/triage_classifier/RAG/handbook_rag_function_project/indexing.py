from __future__ import annotations

from pathlib import Path
import json
import pickle
from typing import List

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


def simple_tokenize(text: str) -> list[str]:
    return [t for t in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in text).split() if t]


def build_indices(chunks: List[dict], artifacts_dir: str, embedding_model_name: str) -> dict:
    p = Path(artifacts_dir)
    p.mkdir(parents=True, exist_ok=True)

    chunks_path = p / 'handbook_chunks.json'
    with open(chunks_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    corpus_tokens = [simple_tokenize(c['content']) for c in chunks]
    bm25 = BM25Okapi(corpus_tokens)
    with open(p / 'bm25.pkl', 'wb') as f:
        pickle.dump(bm25, f)

    model = SentenceTransformer(embedding_model_name)
    texts = [c['content'] for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True).astype('float32')
    np.save(p / 'embeddings.npy', embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, str(p / 'faiss.index'))

    meta = {'embedding_model_name': embedding_model_name, 'num_chunks': len(chunks), 'embedding_dim': dim}
    with open(p / 'index_meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta
