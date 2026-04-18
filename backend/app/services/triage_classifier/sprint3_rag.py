from __future__ import annotations

from pathlib import Path
from typing import Dict
import json
import sys


BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR / "RAG"
DEFAULT_CONFIG_PATH = RAG_DIR / "configs" / "app_config.yaml"

_LLM_RAG_PREDICT = None


def _load_llm_rag_predict():
    """
    Lazily load RAG pipeline entrypoint.
    """
    global _LLM_RAG_PREDICT

    if _LLM_RAG_PREDICT is not None:
        return _LLM_RAG_PREDICT

    rag_root = str(RAG_DIR)
    if rag_root not in sys.path:
        sys.path.insert(0, rag_root)

    try:
        from handbook_rag_function_project.pipeline import llm_rag_predict
    except ImportError as exc:
        raise ImportError(
            "Failed to import RAG pipeline. Ensure RAG dependencies are installed."
        ) from exc

    _LLM_RAG_PREDICT = llm_rag_predict
    return _LLM_RAG_PREDICT


def _resolve_config_path() -> Path:
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH

    example_path = RAG_DIR / "configs" / "app_config.example.yaml"
    if example_path.exists():
        return example_path

    raise FileNotFoundError(
        f"RAG config not found. Expected: {DEFAULT_CONFIG_PATH} or {example_path}"
    )


def predict_ats(text: str) -> Dict[str, float | int]:
    """
    RAG (LLM branch) ATS classification interface.

    Args:
        text: Free-text triage input.

    Returns:
        {
            "ats_category": int,
            "confidence": float  # 0.0 ~ 1.0; -1 if unavailable
        }
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text cannot be empty.")

    llm_rag_predict = _load_llm_rag_predict()
    config_path = _resolve_config_path()

    result = llm_rag_predict(text.strip(), str(config_path))

    ats_category = int(result["ats_category"])
    confidence = result.get("confidence")
    if confidence is None:
        confidence = -1
    else:
        confidence = round(float(confidence), 4)

    return {
        "ats_category": ats_category,
        "confidence": confidence,
    }


def read_input_text() -> str:
    """
    Read from a file path argument if provided, otherwise from stdin.
    """
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        return input_path.read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise ValueError(
        "No input provided. Use either:\n"
        "  python sprint3_rag.py path/to/file.txt\n"
        "or:\n"
        "  python sprint3_rag.py < path/to/file.txt"
    )


def main():
    try:
        input_text = read_input_text()
        if not input_text.strip():
            raise ValueError("Input text is empty.")

        result = predict_ats(input_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
