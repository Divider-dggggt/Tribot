"""Research-only safety-cost-aware DeBERTa for ATS classification.

Ordinary multiclass cross-entropy treats all wrong labels too similarly.
In triage, under-triage (predicting a less urgent category than gold) is
clinically more dangerous than over-triage. This module implements a
safety-cost-aware loss:

    loss = CE + alpha * expected_safety_cost

For a probability vector p over ATS 1-5 and gold label y:

    expected_safety_cost = sum_k p_k * C(y, k)

    C(y, k) = 0                          if k == y
            = lambda_under * (k - y)^2   if k > y   (under-triage)
            = lambda_over * (y - k)      if k < y   (over-triage)

Defaults: alpha = 0.2, lambda_under = 5.0, lambda_over = 1.0.

This does NOT replace the production DeBERTa classifier
(`sprint2_deberta_classifier.py`). Training is never run automatically by
the benchmark; it must be invoked explicitly (see
`train_safety_cost_deberta`).
"""

from __future__ import annotations

import json
from pathlib import Path

ATS_CLASSES = [1, 2, 3, 4, 5]
NUM_CLASSES = len(ATS_CLASSES)


def build_safety_cost_vector(
    gold_label: int,
    lambda_under: float = 5.0,
    lambda_over: float = 1.0,
) -> list[float]:
    """Cost C(y, k) for each possible predicted ATS k in 1..5 given gold y."""
    if not isinstance(gold_label, int) or isinstance(gold_label, bool) or not 1 <= gold_label <= 5:
        raise ValueError(f"ATS gold label must be an integer in 1-5, got {gold_label!r}")

    costs = []
    for k in ATS_CLASSES:
        if k == gold_label:
            costs.append(0.0)
        elif k > gold_label:
            costs.append(float(lambda_under) * float(k - gold_label) ** 2)
        else:
            costs.append(float(lambda_over) * float(gold_label - k))
    return costs


def expected_safety_cost_loss(
    logits,
    gold_labels,
    alpha: float = 0.2,
    lambda_under: float = 5.0,
    lambda_over: float = 1.0,
):
    """Safety-cost-aware loss: CE + alpha * expected safety cost.

    Args:
        logits: tensor of shape (batch, 5) over ATS classes 1..5
                (index 0 -> ATS 1, ..., index 4 -> ATS 5).
        gold_labels: tensor of shape (batch,) with ATS labels 1..5, or
                class indices 0..4 (detected automatically).

    Returns:
        Scalar torch loss: ce_loss + alpha * expected_cost.
    """
    import torch
    import torch.nn.functional as F

    if not torch.is_tensor(logits):
        logits = torch.tensor(logits, dtype=torch.float)
    if not torch.is_tensor(gold_labels):
        gold_labels = torch.tensor(gold_labels, dtype=torch.long)
    gold_labels = gold_labels.to(logits.device).long()

    # Accept either ATS labels (1..5) or class indices (0..4).
    if int(gold_labels.min().item()) >= 1 and int(gold_labels.max().item()) <= 5:
        gold_ats = gold_labels
    elif int(gold_labels.min().item()) >= 0 and int(gold_labels.max().item()) <= 4:
        gold_ats = gold_labels + 1
    else:
        raise ValueError("gold_labels must be ATS labels 1-5 or class indices 0-4")

    class_indices = gold_ats - 1
    ce_loss = F.cross_entropy(logits, class_indices)

    probs = torch.softmax(logits, dim=-1)
    cost_matrix = torch.tensor(
        [
            build_safety_cost_vector(int(y), lambda_under=lambda_under, lambda_over=lambda_over)
            for y in gold_ats.tolist()
        ],
        dtype=probs.dtype,
        device=probs.device,
    )
    expected_cost = (probs * cost_matrix).sum(dim=-1).mean()

    return ce_loss + alpha * expected_cost


class SafetyCostDebertaClassifier:
    """Inference wrapper for a trained safety-cost-aware DeBERTa model.

    The model is a standard 5-class sequence classifier; only its training
    loss differs from the production model, so inference mirrors the
    production wrapper.
    """

    def __init__(self, model_dir: str | Path):
        from .model_runners import ensure_transformers_compat

        ensure_transformers_compat()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Missing dependencies for safety-cost DeBERTa inference. "
                "Install `torch` and `transformers`."
            ) from exc

        model_dir = Path(model_dir)
        if not model_dir.exists():
            raise FileNotFoundError(f"Safety-cost model directory not found: {model_dir}")

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        if int(self.model.config.num_labels) != NUM_CLASSES:
            raise ValueError(
                f"Safety-cost model must have {NUM_CLASSES} output logits, "
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
            logits = self.model(**encoded).logits
            probs = torch.softmax(logits, dim=-1)[0]

        pred_idx = int(torch.argmax(probs).item())
        id2label = getattr(self.model.config, "id2label", {}) or {}
        label_value = id2label.get(pred_idx, id2label.get(str(pred_idx), str(pred_idx + 1)))
        try:
            ats_category = int(label_value)
        except (TypeError, ValueError):
            ats_category = pred_idx + 1

        return {
            "ats_category": ats_category,
            "confidence": round(float(probs[pred_idx].item()), 4),
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


def train_safety_cost_deberta(
    dataset_path: str | Path,
    output_dir: str | Path,
    base_model: str = "microsoft/deberta-v3-small",
    text_field: str = "dialogue_text",
    label_field: str = "ats_category",
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    max_length: int = 512,
    alpha: float = 0.2,
    lambda_under: float = 5.0,
    lambda_over: float = 1.0,
) -> dict:
    """Explicitly train a safety-cost-aware DeBERTa model (research-only).

    This is never called by the benchmark automatically.
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
        num_labels=NUM_CLASSES,
        id2label={i: str(i + 1) for i in range(NUM_CLASSES)},
        label2id={str(i + 1): i for i in range(NUM_CLASSES)},
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    class _AtsDataset(Dataset):
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
            return {
                "input_ids": encoded["input_ids"][0],
                "attention_mask": encoded["attention_mask"][0],
                "gold_ats": torch.tensor(labels[idx], dtype=torch.long),
            }

    loader = DataLoader(_AtsDataset(), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

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
            loss = expected_safety_cost_loss(
                logits,
                batch["gold_ats"].to(device),
                alpha=alpha,
                lambda_under=lambda_under,
                lambda_over=lambda_over,
            )
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
        mean_loss = total_loss / max(1, len(loader))
        history.append({"epoch": epoch + 1, "mean_safety_cost_loss": mean_loss})
        print(f"[safety_cost_deberta] epoch {epoch + 1}/{epochs} loss={mean_loss:.4f}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "training_history.json").write_text(
        json.dumps(
            {
                "alpha": alpha,
                "lambda_under": lambda_under,
                "lambda_over": lambda_over,
                "history": history,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"output_dir": str(output_dir), "history": history}


def evaluate_safety_cost_deberta(
    model_dir: str | Path,
    dataset_path: str | Path,
    text_field: str = "dialogue_text",
    label_field: str = "ats_category",
) -> dict:
    """Evaluate a trained safety-cost DeBERTa model with the benchmark metrics."""
    from .metrics import compute_ats_metrics

    classifier = SafetyCostDebertaClassifier(model_dir)
    texts, labels = _load_training_records(dataset_path, text_field, label_field)
    preds = [classifier.predict_ats(text)["ats_category"] for text in texts]
    return compute_ats_metrics(labels, preds)
