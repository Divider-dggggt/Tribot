#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed as hf_set_seed,
)

LABELS = [1, 2, 3, 4, 5]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}

LEAK_PATTERNS = [
    r"\bATS\s*(Level\s*)?[1-5]\b",
    r"\bcategory\s*[1-5]\b",
    r"within\s+10\s+minutes",
    r"within\s+30\s+minutes",
    r"within\s+60\s+minutes",
    r"within\s+120\s+minutes",
    r"clinical summary",
    r"I(?:'m| am) assigning you",
    r"triaging you as",
    r"priority\s*[1-5]",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train DeBERTa ATS multiclass classifier")
    p.add_argument("--train_json", default="/home/ubuntu/test/generated_scenarios.json")
    p.add_argument("--val_json", default="/home/ubuntu/test/scenarios.json")
    p.add_argument("--output_dir", default="./runs/deberta_multiclass")
    p.add_argument("--model_name", default="microsoft/deberta-v3-base")
    p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--eval_batch_size", type=int, default=16)
    p.add_argument("--grad_accum", type=int, default=1)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--weight_decay", type=float, default=0.01)
    p.add_argument("--warmup_ratio", type=float, default=0.1)
    p.add_argument("--max_length", type=int, default=384)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--use_header", action="store_true")
    p.add_argument("--strip_label_leakage", action="store_true")
    p.add_argument("--no_class_weights", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--bf16", action="store_true")
    return p.parse_args()


def set_all_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    hf_set_seed(seed)


def load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a list")
    return rows


def strip_leakage(text: str) -> str:
    out = text
    for pat in LEAK_PATTERNS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def build_dataframe(rows: List[Dict[str, Any]], use_header: bool, strip_label_leakage: bool) -> pd.DataFrame:
    cleaned = []
    for i, row in enumerate(rows):
        if "dialogue_text" not in row or "ats_category" not in row:
            continue
        try:
            label = int(row["ats_category"])
        except Exception:
            continue
        if label not in LABEL_TO_ID:
            continue
        text = str(row["dialogue_text"]).strip()
        if strip_label_leakage:
            text = strip_leakage(text)
        if use_header and row.get("scenario_summary_header"):
            text = f"{row['scenario_summary_header'].strip()}\n\n{text}"
        cleaned.append(
            {
                "scenario_number": row.get("scenario_number", f"row-{i}"),
                "scenario_summary_header": row.get("scenario_summary_header", ""),
                "dialogue_text": row.get("dialogue_text", ""),
                "text": text,
                "ats_category": label,
                "label": LABEL_TO_ID[label],
            }
        )
    df = pd.DataFrame(cleaned)
    if df.empty:
        raise ValueError("No valid rows found after cleaning")
    return df


class JsonDataset(torch.utils.data.Dataset):
    def __init__(self, df: pd.DataFrame, tokenizer, max_length: int):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]
        enc = self.tokenizer(
            row["text"],
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        enc["labels"] = int(row["label"])
        return enc


class WeightedTrainer(Trainer):
    def __init__(self, class_weights: torch.Tensor | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        if self.class_weights is not None:
            weight = self.class_weights.to(logits.device)
            loss_fct = nn.CrossEntropyLoss(weight=weight)
        else:
            loss_fct = nn.CrossEntropyLoss()
        loss = loss_fct(logits.view(-1, model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    true_ats = np.vectorize(ID_TO_LABEL.get)(labels)
    pred_ats = np.vectorize(ID_TO_LABEL.get)(preds)
    return {
        "accuracy": float(accuracy_score(labels, preds)),
        "macro_f1": float(f1_score(labels, preds, average="macro")),
        "weighted_f1": float(f1_score(labels, preds, average="weighted")),
        "under_triage_rate": float(np.mean(pred_ats > true_ats)),
        "over_triage_rate": float(np.mean(pred_ats < true_ats)),
    }


# def save_summary(out_dir: Path, trainer: Trainer, model, tokenizer, val_df: pd.DataFrame, args: argparse.Namespace) -> None:
#     val_ds = JsonDataset(val_df, tokenizer, args.max_length)
#     pred_output = trainer.predict(val_ds)
#     logits = pred_output.predictions
#     labels = pred_output.label_ids
#     preds = np.argmax(logits, axis=-1)

#     summary = compute_metrics((logits, labels))
#     summary["confusion_matrix"] = confusion_matrix(labels, preds, labels=list(range(len(LABELS)))).tolist()
#     summary["classification_report"] = classification_report(
#         labels,
#         preds,
#         labels=list(range(len(LABELS))),
#         target_names=[str(x) for x in LABELS],
#         output_dict=True,
#         zero_division=0,
#     )

#     pred_df = val_df.copy()
#     pred_df["pred_label_id"] = preds
#     pred_df["pred_ats"] = [ID_TO_LABEL[int(x)] for x in preds]
#     pred_df["true_ats"] = [ID_TO_LABEL[int(x)] for x in labels]
#     pred_df.to_csv(out_dir / "val_predictions.csv", index=False)

#     with open(out_dir / "summary_metrics.json", "w", encoding="utf-8") as f:
#         json.dump(summary, f, ensure_ascii=False, indent=2)

#     with open(out_dir / "label_mapping.json", "w", encoding="utf-8") as f:
#         json.dump({"label_to_id": LABEL_TO_ID, "id_to_label": ID_TO_LABEL}, f, ensure_ascii=False, indent=2)

#     with open(out_dir / "run_args.json", "w", encoding="utf-8") as f:
#         json.dump(vars(args), f, ensure_ascii=False, indent=2)

def save_summary(out_dir: Path, trainer: Trainer, model, tokenizer, val_df: pd.DataFrame, args: argparse.Namespace) -> None:
    val_ds = JsonDataset(val_df, tokenizer, args.max_length)
    pred_output = trainer.predict(val_ds)
    logits = pred_output.predictions
    labels = pred_output.label_ids
    preds = np.argmax(logits, axis=-1)

    sample_model_eval = build_sample_model_eval(labels, preds)

    pred_df = val_df.copy()
    pred_df["pred_label_id"] = preds
    pred_df["pred_ats"] = [ID_TO_LABEL[int(x)] for x in preds]
    pred_df["true_ats"] = [ID_TO_LABEL[int(x)] for x in labels]
    pred_df.to_csv(out_dir / "val_predictions.csv", index=False)

    with open(out_dir / "summary_metrics.json", "w", encoding="utf-8") as f:
        json.dump(sample_model_eval, f, ensure_ascii=False, indent=2)

    with open(out_dir / "label_mapping.json", "w", encoding="utf-8") as f:
        json.dump({"label_to_id": LABEL_TO_ID, "id_to_label": ID_TO_LABEL}, f, ensure_ascii=False, indent=2)

    with open(out_dir / "run_args.json", "w", encoding="utf-8") as f:
        json.dump(vars(args), f, ensure_ascii=False, indent=2)

def build_sample_model_eval(y_true, y_pred):
    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2, 3, 4],
        target_names=["1", "2", "3", "4", "5"],
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4])

    weighted = report["weighted avg"]

    return {
        "sample_model_eval": {
            "f1_score": float(weighted["f1-score"]),
            "precision": float(weighted["precision"]),
            "recall": float(weighted["recall"]),
            "confusion_matrix": cm.tolist(),
        }
    }


def main() -> None:
    args = parse_args()
    set_all_seeds(args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = build_dataframe(load_json(args.train_json), args.use_header, args.strip_label_leakage)
    val_df = build_dataframe(load_json(args.val_json), args.use_header, args.strip_label_leakage)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABELS),
        id2label={i: str(ID_TO_LABEL[i]) for i in ID_TO_LABEL},
        label2id={str(k): v for k, v in LABEL_TO_ID.items()},
    )

    train_ds = JsonDataset(train_df, tokenizer, args.max_length)
    val_ds = JsonDataset(val_df, tokenizer, args.max_length)
    collator = DataCollatorWithPadding(tokenizer=tokenizer)

    class_weights = None
    if not args.no_class_weights:
        weights = compute_class_weight(
            class_weight="balanced",
            classes=np.array(sorted(train_df["label"].unique())),
            y=train_df["label"].to_numpy(),
        )
        full_weights = np.ones(len(LABELS), dtype=np.float32)
        for cls, w in zip(sorted(train_df["label"].unique()), weights):
            full_weights[int(cls)] = float(w)
        class_weights = torch.tensor(full_weights, dtype=torch.float32)

    train_args = TrainingArguments(
        output_dir=str(out_dir),
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        logging_steps=20,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        fp16=args.fp16,
        bf16=args.bf16,
        report_to="none",
    )

    trainer = WeightedTrainer(
        model=model,
        args=train_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
    )

    trainer.train()
    trainer.save_model(str(out_dir / "best_model"))
    tokenizer.save_pretrained(str(out_dir / "best_model"))
    save_summary(out_dir, trainer, model, tokenizer, val_df, args)
    print(f"done: {out_dir}")


if __name__ == "__main__":
    main()
