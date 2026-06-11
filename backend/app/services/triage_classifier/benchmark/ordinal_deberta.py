"""Research-only ordinal DeBERTa for ATS classification.

ATS is an ordinal scale (ATS 1 < ATS 2 < ... < ATS 5, smaller = more
urgent), not an unordered 5-class task. This module implements the
cumulative ordinal formulation:

    For ATS labels 1-5, create 4 binary targets
        t_k = 1 if y <= k else 0,  k = 1, 2, 3, 4

    The model outputs 4 logits z_1..z_4 with
        P(y <= k | x) = sigmoid(z_k)

    Training loss:
        L_ord = sum_k BCEWithLogitsLoss(z_k, t_k)

This does NOT replace the production DeBERTa classifier
(`sprint2_deberta_classifier.py`). Training is never run automatically by
the benchmark; it must be invoked explicitly (see `train_ordinal_deberta`).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

NUM_THRESHOLDS = 4  # k = 1..4 for ATS labels 1..5


def label_to_ordinal_targets(label: int) -> list[int]:
    """Convert ATS label 1-5 into 4 cumulative binary targets.

    Examples:
        1 -> [1, 1, 1, 1]
        2 -> [0, 1, 1, 1]
        5 -> [0, 0, 0, 0]
    """
    if not isinstance(label, int) or isinstance(label, bool) or not 1 <= label <= 5:
        raise ValueError(f"ATS label must be an integer in 1-5, got {label!r}")
    return [1 if label <= k else 0 for k in range(1, NUM_THRESHOLDS + 1)]


def ordinal_logits_to_probs(logits) -> list[float]:
    """Apply sigmoid to 4 ordinal logits: P(y <= k | x) = sigmoid(z_k)."""
    values = [float(z) for z in logits]
    if len(values) != NUM_THRESHOLDS:
        raise ValueError(f"Expected {NUM_THRESHOLDS} ordinal logits, got {len(values)}")
    return [1.0 / (1.0 + math.exp(-z)) for z in values]


def ordinal_probs_to_label(probs, threshold: float = 0.5) -> int:
    """Convert cumulative probabilities back to an ATS label.

    Count how many cumulative thresholds are true:
        4 true -> ATS 1, 3 true -> ATS 2, ..., 0 true -> ATS 5.
    """
    values = [float(p) for p in probs]
    if len(values) != NUM_THRESHOLDS:
        raise ValueError(f"Expected {NUM_THRESHOLDS} probabilities, got {len(values)}")
    num_true = sum(1 for p in values if p >= threshold)
    return 5 - num_true


def _label_probs_from_cumulative(cum_probs: list[float]) -> list[float]:
    """Derive per-label probabilities P(y = k) from cumulative P(y <= k).

    Uses P(y = k) = P(y <= k) - P(y <= k-1) with P(y <= 0) = 0 and
    P(y <= 5) = 1; clamped at 0 since the raw sigmoids are not guaranteed
    monotone.
    """
    extended = [0.0] + list(cum_probs) + [1.0]
    return [max(0.0, extended[k] - extended[k - 1]) for k in range(1, 6)]


class OrdinalDebertaClassifier:
    """Inference wrapper for a trained ordinal DeBERTa model (4 logits)."""

    def __init__(self, model_dir: str | Path):
        from .model_runners import ensure_transformers_compat

        ensure_transformers_compat()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Missing dependencies for ordinal DeBERTa inference. "
                "Install `torch` and `transformers`."
            ) from exc

        model_dir = Path(model_dir)
        if not model_dir.exists():
            raise FileNotFoundError(f"Ordinal model directory not found: {model_dir}")

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        if int(self.model.config.num_labels) != NUM_THRESHOLDS:
            raise ValueError(
                f"Ordinal model must have {NUM_THRESHOLDS} output logits, "
                f"found num_labels={self.model.config.num_labels}"
            )
        self.model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def predict_ats(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text cannot be empty.")

        torch = self._torch
        encoded = self.tokenizer(
            text.strip(), return_tensors="pt", truncation=True, max_length=512
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            logits = self.model(**encoded).logits[0]

        cum_probs = ordinal_logits_to_probs(logits.tolist())
        label = ordinal_probs_to_label(cum_probs)
        label_probs = _label_probs_from_cumulative(cum_probs)
        return {
            "ats_category": label,
            "confidence": round(float(label_probs[label - 1]), 4),
            "cumulative_probs": [round(p, 4) for p in cum_probs],
        }


def _load_training_records(dataset_path: str | Path, text_field: str, label_field: str):
    records = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    texts, labels = [], []
    for record in records:
        text = record.get(text_field)
        label = record.get(label_field)
        if not text or label is None:
            continue
        label = int(label)
        if 1 <= label <= 5:
            texts.append(str(text))
            labels.append(label)
    if not texts:
        raise ValueError(f"No usable records in {dataset_path}")
    return texts, labels


def train_ordinal_deberta(
    dataset_path: str | Path,
    output_dir: str | Path,
    base_model: str = "microsoft/deberta-v3-small",
    text_field: str = "dialogue_text",
    label_field: str = "ats_category",
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    max_length: int = 512,
) -> dict:
    """Explicitly train an ordinal DeBERTa model (research-only).

    This is never called by the benchmark automatically. Run it manually,
    e.g.:

        python -c "from backend.app.services.triage_classifier.benchmark \
            .ordinal_deberta import train_ordinal_deberta; \
            train_ordinal_deberta('data.json', 'out_dir')"
    """
    from .model_runners import ensure_transformers_compat

    ensure_transformers_compat()
    import torch
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    texts, labels = _load_training_records(dataset_path, text_field, label_field)
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model,
        num_labels=NUM_THRESHOLDS,
        problem_type="multi_label_classification",
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    class _OrdinalDataset(Dataset):
        def __len__(self):
            return len(texts)

        def __getitem__(self, idx):
            encoded = tokenizer(
                texts[idx],
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt",
            )
            targets = torch.tensor(
                label_to_ordinal_targets(labels[idx]), dtype=torch.float
            )
            return {
                "input_ids": encoded["input_ids"][0],
                "attention_mask": encoded["attention_mask"][0],
                "targets": targets,
            }

    loader = DataLoader(_OrdinalDataset(), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    model.train()
    history = []
    for epoch in range(epochs):
        total_loss = 0.0
        for batch in loader:
            optimizer.zero_grad()
            logits = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
            ).logits
            loss = loss_fn(logits, batch["targets"].to(device))
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
        mean_loss = total_loss / max(1, len(loader))
        history.append({"epoch": epoch + 1, "mean_ordinal_bce_loss": mean_loss})
        print(f"[ordinal_deberta] epoch {epoch + 1}/{epochs} loss={mean_loss:.4f}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "training_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    return {"output_dir": str(output_dir), "history": history}


def evaluate_ordinal_deberta(
    model_dir: str | Path,
    dataset_path: str | Path,
    text_field: str = "dialogue_text",
    label_field: str = "ats_category",
) -> dict:
    """Evaluate a trained ordinal DeBERTa model with the benchmark metrics."""
    from .metrics import compute_ats_metrics

    classifier = OrdinalDebertaClassifier(model_dir)
    texts, labels = _load_training_records(dataset_path, text_field, label_field)
    preds = [classifier.predict_ats(text)["ats_category"] for text in texts]
    return compute_ats_metrics(labels, preds)
