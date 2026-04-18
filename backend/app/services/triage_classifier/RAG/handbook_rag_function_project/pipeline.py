from __future__ import annotations

from pathlib import Path

from .config import load_config
from .chunking import parse_pdf_to_chunks, chunks_to_dicts
from .indexing import build_indices
from .retrieval import Retriever
from .normalize import handbook_fit
from .local_models import LocalClassifier
from .llm_branch import llm_classify_and_explain


def ingest_handbook(config_path: str) -> dict:
    cfg = load_config(config_path)
    chunks = parse_pdf_to_chunks(
        cfg['paths']['handbook_pdf'],
        chunk_size_chars=cfg['retrieval'].get('chunk_size_chars', 1400),
        chunk_overlap_chars=cfg['retrieval'].get('chunk_overlap_chars', 200),
    )
    meta = build_indices(chunks_to_dicts(chunks), cfg['paths']['artifacts_dir'], cfg['retrieval']['embedding_model_name'])
    return {'status': 'ok', **meta}


def _shared_prepare(query_txt: str, config_path: str) -> tuple[dict, dict]:
    cfg = load_config(config_path)
    retriever = Retriever(cfg['paths']['artifacts_dir'])
    chunks = retriever.retrieve(
        query_txt,
        bm25_top_k=cfg['retrieval'].get('bm25_top_k', 8),
        vector_top_k=cfg['retrieval'].get('vector_top_k', 8),
        final_top_k=cfg['retrieval'].get('final_top_k', 6),
    )
    fit = handbook_fit(query_txt, chunks)
    return cfg, fit


def local_predict(query_txt: str, config_path: str) -> dict:
    cfg, fit = _shared_prepare(query_txt, config_path)
    clf = LocalClassifier(cfg)
    return clf.predict(fit['augmented_text'])


def llm_rag_predict(query_txt: str, config_path: str) -> dict:
    cfg, fit = _shared_prepare(query_txt, config_path)
    return llm_classify_and_explain(query_txt, fit, cfg)
