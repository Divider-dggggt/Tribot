"""Lightweight wrappers around the existing production ATS models.

Each `predict_with_*` function calls the corresponding existing wrapper in
`backend/app/services/triage_classifier/` and returns a uniform dict:

    {
        "ats_category": int | None,
        "confidence": float | None,
        "error": str | None,
    }

Model failures never raise; they are recorded in the "error" field so the
benchmark can continue with the remaining models.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

from .metrics import normalize_ats

TRIAGE_CLASSIFIER_DIR = Path(__file__).resolve().parent.parent

_MODULE_CACHE: dict[str, object] = {}

_COMPAT_APPLIED = False


def ensure_transformers_compat() -> None:
    """Benchmark-local workaround for a broken global `deepspeed` install.

    On this server an old `deepspeed` package (importing the removed
    `torch._six`) is installed, and `transformers` imports it eagerly when
    present, which breaks all DeBERTa model loading. If `deepspeed` cannot
    be imported, register an inert stub so `transformers` can proceed.
    Plain CPU/GPU inference never touches deepspeed functionality, and the
    Python environment itself is not modified.
    """
    global _COMPAT_APPLIED
    if _COMPAT_APPLIED:
        return
    _COMPAT_APPLIED = True
    try:
        import deepspeed  # noqa: F401
    except Exception:
        stub = types.ModuleType("deepspeed")
        stub.__version__ = "0.0.0-benchmark-stub"
        stub.__spec__ = importlib.machinery.ModuleSpec("deepspeed", loader=None)
        sys.modules["deepspeed"] = stub


def _load_module(module_name: str, filename: str):
    """Import an existing wrapper module directly from its file path.

    Using file-path imports keeps the benchmark independent of how the
    project packages are laid out and does not require changing production
    code.
    """
    if module_name in _MODULE_CACHE:
        return _MODULE_CACHE[module_name]

    file_path = TRIAGE_CLASSIFIER_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Wrapper file not found: {file_path}")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _MODULE_CACHE[module_name] = module
    return module


def _empty_result() -> dict:
    return {"ats_category": None, "confidence": None, "error": None}


def _run_predict_ats(module_name: str, filename: str, text: str, *, confidence_is_percent: bool = False) -> dict:
    result = _empty_result()
    try:
        module = _load_module(module_name, filename)
        raw = module.predict_ats(text)
        result["ats_category"] = normalize_ats(raw["ats_category"])
        confidence = raw.get("confidence")
        if confidence is not None:
            confidence = float(confidence)
            if confidence_is_percent:
                confidence = confidence / 100.0
            result["confidence"] = confidence
    except Exception as exc:  # noqa: BLE001 - record any failure and continue
        result["ats_category"] = None
        result["confidence"] = None
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def predict_with_baseline(text: str) -> dict:
    """Baseline TF-IDF + classical ML model (confidence reported in percent upstream)."""
    return _run_predict_ats(
        "tribot_benchmark_baseline_predict",
        "baseline_predict.py",
        text,
        confidence_is_percent=True,
    )


def predict_with_deberta(text: str) -> dict:
    """Production DeBERTa sequence classifier."""
    ensure_transformers_compat()
    return _run_predict_ats(
        "tribot_benchmark_sprint2_deberta_classifier",
        "sprint2_deberta_classifier.py",
        text,
    )


def predict_with_setfit(text: str) -> dict:
    """Production SetFit classifier."""
    ensure_transformers_compat()
    return _run_predict_ats(
        "tribot_benchmark_sprint2_setfit_classifier",
        "sprint2_setfit_classifier.py",
        text,
    )


_RAG_LOCAL_CONFIG: Path | None = None


def _prepare_local_rag_config() -> Path | None:
    """Build a benchmark-local copy of the RAG app config with local paths.

    The production `app_config.yaml` contains Docker container paths
    (`/app/...`). For local benchmark runs we rewrite only the `paths`
    section to point at the actual files in this checkout and write the
    result to a temporary file. The production config file is not modified.
    Returns None if the local config cannot be prepared.
    """
    global _RAG_LOCAL_CONFIG
    if _RAG_LOCAL_CONFIG is not None:
        return _RAG_LOCAL_CONFIG
    try:
        import tempfile

        import yaml

        rag_dir = TRIAGE_CLASSIFIER_DIR / "RAG"
        source = rag_dir / "configs" / "app_config.yaml"
        if not source.exists():
            source = rag_dir / "configs" / "app_config.example.yaml"
        config = yaml.safe_load(source.read_text(encoding="utf-8"))

        paths = config.get("paths", {})
        local_paths = {
            "handbook_pdf": rag_dir / "assets" / Path(str(paths.get("handbook_pdf", ""))).name,
            "llm_config_yaml": rag_dir / "configs" / Path(str(paths.get("llm_config_yaml", "llm_config.yaml"))).name,
            "artifacts_dir": rag_dir / "artifacts",
        }
        for key, local in local_paths.items():
            configured = Path(str(paths.get(key, "")))
            if not configured.exists():
                paths[key] = str(local)
        config["paths"] = paths

        tmp = tempfile.NamedTemporaryFile(
            "w",
            suffix=".yaml",
            prefix="tribot_benchmark_rag_config_",
            delete=False,
            encoding="utf-8",
        )
        with tmp:
            yaml.safe_dump(config, tmp)
        _RAG_LOCAL_CONFIG = Path(tmp.name)
        return _RAG_LOCAL_CONFIG
    except Exception:  # noqa: BLE001 - fall back to the wrapper's own config
        return None


def predict_with_rag(text: str) -> dict:
    """RAG + handbook ATS classification model (LLM branch)."""
    ensure_transformers_compat()
    result = _empty_result()
    try:
        module = _load_module("tribot_benchmark_sprint3_rag", "sprint3_rag.py")
        local_config = _prepare_local_rag_config()
        if local_config is not None:
            # Patch only the benchmark's in-memory module copy.
            module.DEFAULT_CONFIG_PATH = local_config
        raw = module.predict_ats(text)
        result["ats_category"] = normalize_ats(raw["ats_category"])
        if raw.get("confidence") is not None:
            result["confidence"] = float(raw["confidence"])
    except Exception as exc:  # noqa: BLE001 - record any failure and continue
        result["ats_category"] = None
        result["confidence"] = None
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def predict_with_rule(text: str) -> dict:
    """Rule-based severity engine (safety coverage layer).

    Returns the uniform prediction dict; the full `severity_result` from
    `flag_high_severity` is attached under "severity_result" so callers can
    build the benchmark-only rule energy summary without re-running rules.
    """
    result = _empty_result()
    result["severity_result"] = None
    try:
        module = _load_module(
            "tribot_benchmark_severity_flagging", "severity_flagging.py"
        )
        severity_result = module.flag_high_severity(text)
        result["severity_result"] = severity_result
        recommended = severity_result.get("recommended_ats_category")
        if recommended is not None:
            result["ats_category"] = normalize_ats(recommended)
    except Exception as exc:  # noqa: BLE001 - record any failure and continue
        result["ats_category"] = None
        result["confidence"] = None
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def apply_rule_coverage(model_ats: int | None, rule_ats: int | None) -> int | None:
    """Safety-Dominant Fusion Rule.

    Since lower ATS values mean higher urgency, taking the minimum guarantees
    the final output is never less urgent than the rule recommendation:

        y_final = min(y_model, y_rule)
    """

    def _valid(value) -> int | None:
        try:
            return normalize_ats(value)
        except (ValueError, TypeError):
            return None

    model_valid = _valid(model_ats)
    rule_valid = _valid(rule_ats)

    if model_valid is not None and rule_valid is not None:
        return min(model_valid, rule_valid)
    if model_valid is not None:
        return model_valid
    if rule_valid is not None:
        return rule_valid
    return None
