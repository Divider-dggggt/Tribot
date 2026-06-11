"""ATS safety metrics for the triage classification benchmark.

ATS convention:
    ATS 1 is most urgent, ATS 5 is least urgent. Smaller number means more
    urgent. Therefore:
        under-triage  -> predicted_ats > gold_ats  (clinically dangerous)
        over-triage   -> predicted_ats < gold_ats  (resource cost)
"""

from __future__ import annotations

import re
from typing import Sequence

ATS_CLASSES = [1, 2, 3, 4, 5]

try:
    from sklearn.metrics import (
        confusion_matrix as _sk_confusion_matrix,
        precision_recall_fscore_support as _sk_prfs,
    )

    _SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - sklearn is normally available
    _SKLEARN_AVAILABLE = False


def normalize_ats(value) -> int:
    """Normalize an ATS label such as 1, "1", "ATS 1", "Category 1" to int 1-5.

    Raises:
        ValueError: if the value cannot be interpreted as an ATS category 1-5.
    """
    if isinstance(value, bool):
        raise ValueError(f"Invalid ATS value: {value!r} (boolean is not an ATS category)")

    if isinstance(value, int):
        candidate = value
    elif isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"Invalid ATS value: {value!r} (non-integer float)")
        candidate = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Invalid ATS value: empty string")
        match = re.fullmatch(r"(?:ats|category|cat)?\s*[:\-]?\s*([1-5])(?:\.0)?", text, flags=re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid ATS value: {value!r}")
        candidate = int(match.group(1))
    else:
        raise ValueError(f"Invalid ATS value: {value!r} (unsupported type {type(value).__name__})")

    if candidate not in ATS_CLASSES:
        raise ValueError(f"Invalid ATS value: {value!r} (must be in 1-5)")
    return candidate


def asymmetric_safety_cost(
    gold: int,
    pred: int,
    lambda_under: float = 5.0,
    lambda_over: float = 1.0,
) -> float:
    """Asymmetric ordinal safety cost.

    pred > gold means under-triage (penalized quadratically, weight lambda_under).
    pred < gold means over-triage (penalized linearly, weight lambda_over).
    """
    if pred == gold:
        return 0.0
    if pred > gold:
        return float(lambda_under) * float(pred - gold) ** 2
    return float(lambda_over) * float(gold - pred)


def _max_possible_cost(gold: int, lambda_under: float, lambda_over: float) -> float:
    return max(
        asymmetric_safety_cost(gold, k, lambda_under=lambda_under, lambda_over=lambda_over)
        for k in ATS_CLASSES
    )


def _fallback_prfs(gold_labels: Sequence[int], pred_labels: Sequence[int]):
    """Simple per-class precision/recall/F1 fallback when sklearn is unavailable."""
    precision, recall, f1, support = [], [], [], []
    for cls in ATS_CLASSES:
        tp = sum(1 for g, p in zip(gold_labels, pred_labels) if g == cls and p == cls)
        fp = sum(1 for g, p in zip(gold_labels, pred_labels) if g != cls and p == cls)
        fn = sum(1 for g, p in zip(gold_labels, pred_labels) if g == cls and p != cls)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        precision.append(prec)
        recall.append(rec)
        f1.append(f)
        support.append(sum(1 for g in gold_labels if g == cls))
    return precision, recall, f1, support


def _fallback_confusion_matrix(gold_labels: Sequence[int], pred_labels: Sequence[int]):
    matrix = [[0 for _ in ATS_CLASSES] for _ in ATS_CLASSES]
    for g, p in zip(gold_labels, pred_labels):
        matrix[g - 1][p - 1] += 1
    return matrix


def compute_ats_metrics(
    gold_labels: list[int],
    pred_labels: list[int],
    lambda_under: float = 5.0,
    lambda_over: float = 1.0,
) -> dict:
    """Compute clinically meaningful ordinal safety metrics for ATS predictions.

    Both label lists must contain integers in 1-5 and have the same length.
    """
    if len(gold_labels) != len(pred_labels):
        raise ValueError(
            f"gold_labels and pred_labels length mismatch: {len(gold_labels)} vs {len(pred_labels)}"
        )
    if not gold_labels:
        raise ValueError("Cannot compute metrics on empty label lists.")

    gold = [normalize_ats(g) for g in gold_labels]
    pred = [normalize_ats(p) for p in pred_labels]
    n = len(gold)

    if _SKLEARN_AVAILABLE:
        per_prec, per_rec, per_f1, _ = _sk_prfs(
            gold, pred, labels=ATS_CLASSES, average=None, zero_division=0
        )
        per_prec, per_rec, per_f1 = list(map(float, per_prec)), list(map(float, per_rec)), list(map(float, per_f1))
        _, _, macro_f1, _ = _sk_prfs(gold, pred, labels=ATS_CLASSES, average="macro", zero_division=0)
        _, _, weighted_f1, _ = _sk_prfs(gold, pred, labels=ATS_CLASSES, average="weighted", zero_division=0)
        macro_f1, weighted_f1 = float(macro_f1), float(weighted_f1)
        conf = _sk_confusion_matrix(gold, pred, labels=ATS_CLASSES).tolist()
    else:
        per_prec, per_rec, per_f1, support = _fallback_prfs(gold, pred)
        macro_f1 = sum(per_f1) / len(per_f1)
        total = sum(support)
        weighted_f1 = (
            sum(f * s for f, s in zip(per_f1, support)) / total if total > 0 else 0.0
        )
        conf = _fallback_confusion_matrix(gold, pred)

    exact = sum(1 for g, p in zip(gold, pred) if g == p)
    under = sum(1 for g, p in zip(gold, pred) if p > g)
    over = sum(1 for g, p in zip(gold, pred) if p < g)
    adjacent = sum(1 for g, p in zip(gold, pred) if abs(p - g) <= 1)

    under_severity = sum(max(0, p - g) for g, p in zip(gold, pred)) / n
    squared_under_severity = sum(max(0, p - g) ** 2 for g, p in zip(gold, pred)) / n
    mean_abs_error = sum(abs(p - g) for g, p in zip(gold, pred)) / n

    critical_under = sum(1 for g, p in zip(gold, pred) if g in (1, 2) and p >= 3)

    def _class_recall(cls: int) -> float | None:
        denom = sum(1 for g in gold if g == cls)
        if denom == 0:
            return None
        return sum(1 for g, p in zip(gold, pred) if g == cls and p == cls) / denom

    ats_1_recall = _class_recall(1)
    ats_2_recall = _class_recall(2)
    ats_1_2_denom = sum(1 for g in gold if g in (1, 2))
    ats_1_2_recall = (
        sum(1 for g, p in zip(gold, pred) if g in (1, 2) and p == g) / ats_1_2_denom
        if ats_1_2_denom > 0
        else None
    )

    costs = [
        asymmetric_safety_cost(g, p, lambda_under=lambda_under, lambda_over=lambda_over)
        for g, p in zip(gold, pred)
    ]
    mean_cost = sum(costs) / n
    max_costs = [_max_possible_cost(g, lambda_under, lambda_over) for g in gold]
    mean_max_cost = sum(max_costs) / n
    if mean_max_cost > 0:
        swa = 1.0 - (mean_cost / mean_max_cost)
    else:
        swa = 1.0
    # Clamp only the final value into [0, 1] for safety.
    swa = min(1.0, max(0.0, swa))

    return {
        "num_cases": n,
        "accuracy": exact / n,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class_precision": {str(c): per_prec[i] for i, c in enumerate(ATS_CLASSES)},
        "per_class_recall": {str(c): per_rec[i] for i, c in enumerate(ATS_CLASSES)},
        "per_class_f1": {str(c): per_f1[i] for i, c in enumerate(ATS_CLASSES)},
        "confusion_matrix": conf,
        "under_triage_rate": under / n,
        "over_triage_rate": over / n,
        "exact_match_rate": exact / n,
        "adjacent_accuracy": adjacent / n,
        "mean_absolute_ordinal_error": mean_abs_error,
        "under_triage_severity_index": under_severity,
        "squared_under_triage_severity_index": squared_under_severity,
        "critical_under_triage_rate": critical_under / n,
        "ats_1_recall": ats_1_recall,
        "ats_2_recall": ats_2_recall,
        "ats_1_2_recall": ats_1_2_recall,
        "asymmetric_safety_cost_mean": mean_cost,
        "safety_weighted_accuracy": swa,
    }
