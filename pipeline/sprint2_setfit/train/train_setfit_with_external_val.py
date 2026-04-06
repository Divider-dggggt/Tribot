#!/usr/bin/env python3
"""Train a SetFit ATS triage classifier with optional external validation data.

Main improvement over the original script:
- supports a separate external validation JSON (for example scenarios.json)
- keeps a held-out test split from the training source JSON
- fixes Python 3.11 dataclass defaults via field(default_factory=...)

Typical usage:
  python train_setfit_with_external_val.py \
      --input_json /home/ubuntu/test/generated_triage_dataset_200.json \
      --external_val_json /home/ubuntu/test/scenarios_formatted.json \
      --output_dir runs/minilm_external_val
"""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

LABELS = [1, 2, 3, 4, 5]
LABEL_TO_INDEX = {label: idx for idx, label in enumerate(LABELS)}
INDEX_TO_LABEL = {idx: label for label, idx in LABEL_TO_INDEX.items()}
REQUIRED_FIELDS = {"scenario_number", "scenario_summary_header", "dialogue_text", "ats_category"}


@dataclass
class SplitConfig:
    test_size: float = 0.15
    val_size: float = 0.15
    seed: int = 42


@dataclass
class TrainConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    num_epochs: int = 4
    num_iterations: int = 20
    body_learning_rate: float = 2e-5
    max_length: int = 256
    use_amp: bool = True
    head_type: str = "logistic"
    end_to_end: bool = False
    head_learning_rate: float = 1e-2
    l2_weight: float = 0.0


@dataclass
class RunConfig:
    input_json: str
    output_dir: str
    external_val_json: Optional[str] = None
    text_field: str = "dialogue_text"
    use_summary_header: bool = False
    split: SplitConfig = field(default_factory=SplitConfig)
    train: TrainConfig = field(default_factory=TrainConfig)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SetFit on ATS triage JSON with optional external validation")
    parser.add_argument("--input_json", type=str, required=True)
    parser.add_argument("--external_val_json", type=str, default=None)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--model_name", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--num_epochs", type=int, default=4)
    parser.add_argument("--num_iterations", type=int, default=20)
    parser.add_argument("--body_learning_rate", type=float, default=2e-5)
    parser.add_argument("--head_learning_rate", type=float, default=1e-2)
    parser.add_argument("--l2_weight", type=float, default=0.0)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test_size", type=float, default=0.15)
    parser.add_argument("--val_size", type=float, default=0.15, help="Only used when no external_val_json is provided.")
    parser.add_argument("--text_field", type=str, default="dialogue_text")
    parser.add_argument("--use_summary_header", action="store_true")
    parser.add_argument("--no_amp", action="store_true")
    parser.add_argument("--head_type", choices=["logistic", "differentiable"], default="logistic")
    parser.add_argument("--end_to_end", action="store_true")
    return parser.parse_args()


def load_rows(input_json: str) -> List[dict]:
    with open(input_json, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError("Expected the JSON file to contain a list of records.")
    for i, row in enumerate(rows):
        missing = REQUIRED_FIELDS - set(row.keys())
        if missing:
            raise ValueError(f"Row {i} is missing fields: {missing}")
        if row["ats_category"] not in LABEL_TO_INDEX:
            raise ValueError(f"Row {i} has invalid ats_category: {row['ats_category']}")
    return rows


def build_text(row: dict, text_field: str, use_summary_header: bool) -> str:
    if text_field not in row:
        raise KeyError(f"text_field={text_field!r} not found in row.")
    text = str(row[text_field]).strip()
    if use_summary_header:
        header = str(row.get("scenario_summary_header", "")).strip()
        if header:
            text = f"{header}\n\n{text}"
    return text


def make_dataframe(rows: List[dict], text_field: str, use_summary_header: bool) -> pd.DataFrame:
    df = pd.DataFrame(rows).copy()
    df["text"] = [build_text(r, text_field=text_field, use_summary_header=use_summary_header) for r in rows]
    df["label"] = df["ats_category"].map(LABEL_TO_INDEX).astype(int)
    keep_cols = ["scenario_number", "scenario_summary_header", "dialogue_text", "ats_category", "text", "label"]
    for maybe_extra in ["ats_note"]:
        if maybe_extra in df.columns:
            keep_cols.insert(4, maybe_extra)
    return df[keep_cols]


def stratified_split(df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.test_size <= 0 or cfg.val_size <= 0 or (cfg.test_size + cfg.val_size) >= 1:
        raise ValueError("Need 0 < test_size, val_size and test_size + val_size < 1")

    train_df, test_df = train_test_split(
        df,
        test_size=cfg.test_size,
        stratify=df["label"],
        random_state=cfg.seed,
    )
    relative_val_size = cfg.val_size / (1.0 - cfg.test_size)
    train_df, val_df = train_test_split(
        train_df,
        test_size=relative_val_size,
        stratify=train_df["label"],
        random_state=cfg.seed,
    )
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def split_with_external_val(train_source_df: pd.DataFrame, external_val_df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.test_size <= 0 or cfg.test_size >= 1:
        raise ValueError("Need 0 < test_size < 1 when using external validation")

    train_df, test_df = train_test_split(
        train_source_df,
        test_size=cfg.test_size,
        stratify=train_source_df["label"],
        random_state=cfg.seed,
    )
    return train_df.reset_index(drop=True), external_val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def to_hf_dataset(df: pd.DataFrame) -> Dataset:
    return Dataset.from_pandas(df[["text", "label"]], preserve_index=False)


def compute_extra_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true_ats = np.vectorize(INDEX_TO_LABEL.get)(y_true)
    y_pred_ats = np.vectorize(INDEX_TO_LABEL.get)(y_pred)
    under_triage = float(np.mean(y_pred_ats > y_true_ats))
    over_triage = float(np.mean(y_pred_ats < y_true_ats))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "under_triage_rate": under_triage,
        "over_triage_rate": over_triage,
    }


def save_split(df: pd.DataFrame, path: Path) -> None:
    df.to_json(path, orient="records", force_ascii=False, indent=2)


def save_label_distribution(df: pd.DataFrame, path: Path) -> None:
    counts = df["ats_category"].value_counts().sort_index().to_dict()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)


def plot_confusion(y_true: np.ndarray, y_pred: np.ndarray, out_path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(LABELS))))
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest")
    fig.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(LABELS)),
        yticks=np.arange(len(LABELS)),
        xticklabels=LABELS,
        yticklabels=LABELS,
        xlabel="Predicted ATS",
        ylabel="True ATS",
        title="Confusion Matrix",
    )
    thresh = cm.max() / 2.0 if cm.max() > 0 else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def maybe_set_cuda_device() -> None:
    local_rank = os.environ.get("LOCAL_RANK")
    if local_rank is None:
        return
    try:
        import torch
        torch.cuda.set_device(int(local_rank))
    except Exception:
        pass


def build_model(cfg: TrainConfig) -> SetFitModel:
    if cfg.head_type == "logistic":
        return SetFitModel.from_pretrained(
            cfg.model_name,
            head_params={"class_weight": "balanced", "max_iter": 1000},
        )
    return SetFitModel.from_pretrained(
        cfg.model_name,
        use_differentiable_head=True,
        head_params={"out_features": len(LABELS)},
    )


def build_training_args(cfg: TrainConfig) -> TrainingArguments:
    common = {
        "batch_size": cfg.batch_size if cfg.head_type == "logistic" else (cfg.batch_size, max(8, cfg.batch_size // 2)),
        "num_epochs": cfg.num_epochs if cfg.head_type == "logistic" else (cfg.num_epochs, max(8, cfg.num_epochs * 2)),
        "body_learning_rate": cfg.body_learning_rate,
        "max_length": cfg.max_length,
        "use_amp": cfg.use_amp,
    }
    if cfg.head_type == "differentiable":
        common.update(
            {
                "end_to_end": cfg.end_to_end,
                "head_learning_rate": cfg.head_learning_rate,
                "l2_weight": cfg.l2_weight,
            }
        )
    return TrainingArguments(**common)


def evaluate_and_save(model: SetFitModel, trainer: Trainer, split_name: str, df: pd.DataFrame, out_dir: Path) -> Dict[str, object]:
    dataset = to_hf_dataset(df)
    trainer_metrics = trainer.evaluate(dataset)
    y_true = df["label"].to_numpy()
    y_pred = np.asarray(model.predict(df["text"].tolist()), dtype=int)

    extra = compute_extra_metrics(y_true, y_pred)
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=[f"ATS_{x}" for x in LABELS],
        output_dict=True,
        zero_division=0,
    )
    prfs = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        zero_division=0,
    )
    per_class = {
        f"ATS_{LABELS[i]}": {
            "precision": float(prfs[0][i]),
            "recall": float(prfs[1][i]),
            "f1": float(prfs[2][i]),
            "support": int(prfs[3][i]),
        }
        for i in range(len(LABELS))
    }

    metrics = {
        "split": split_name,
        "trainer_metrics": {k: float(v) for k, v in trainer_metrics.items() if isinstance(v, (int, float, np.floating))},
        "extra_metrics": extra,
        "per_class": per_class,
        "classification_report": report,
    }

    with open(out_dir / f"{split_name}_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    predictions_df = df.copy()
    predictions_df["pred_label_index"] = y_pred
    predictions_df["pred_ats_category"] = [INDEX_TO_LABEL[idx] for idx in y_pred]
    predictions_df["is_correct"] = predictions_df["pred_ats_category"] == predictions_df["ats_category"]
    predictions_df.to_csv(out_dir / f"{split_name}_predictions.csv", index=False)

    plot_confusion(y_true, y_pred, out_dir / f"{split_name}_confusion_matrix.png")
    return metrics


def main() -> None:
    args = parse_args()
    maybe_set_cuda_device()
    set_seed(args.seed)

    run_cfg = RunConfig(
        input_json=args.input_json,
        external_val_json=args.external_val_json,
        output_dir=args.output_dir,
        text_field=args.text_field,
        use_summary_header=args.use_summary_header,
        split=SplitConfig(test_size=args.test_size, val_size=args.val_size, seed=args.seed),
        train=TrainConfig(
            model_name=args.model_name,
            batch_size=args.batch_size,
            num_epochs=args.num_epochs,
            num_iterations=args.num_iterations,
            body_learning_rate=args.body_learning_rate,
            max_length=args.max_length,
            use_amp=not args.no_amp,
            head_type=args.head_type,
            end_to_end=args.end_to_end,
            head_learning_rate=args.head_learning_rate,
            l2_weight=args.l2_weight,
        ),
    )

    output_dir = Path(run_cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_source_rows = load_rows(run_cfg.input_json)
    train_source_df = make_dataframe(train_source_rows, text_field=run_cfg.text_field, use_summary_header=run_cfg.use_summary_header)

    if run_cfg.external_val_json:
        external_val_rows = load_rows(run_cfg.external_val_json)
        external_val_df = make_dataframe(external_val_rows, text_field=run_cfg.text_field, use_summary_header=run_cfg.use_summary_header)
        train_df, val_df, test_df = split_with_external_val(train_source_df, external_val_df, run_cfg.split)
        split_mode = "external_validation"
    else:
        train_df, val_df, test_df = stratified_split(train_source_df, run_cfg.split)
        split_mode = "internal_random_split"

    save_split(train_df, output_dir / "train_split.json")
    save_split(val_df, output_dir / "val_split.json")
    save_split(test_df, output_dir / "test_split.json")
    save_label_distribution(train_df, output_dir / "train_label_distribution.json")
    save_label_distribution(val_df, output_dir / "val_label_distribution.json")
    save_label_distribution(test_df, output_dir / "test_label_distribution.json")

    with open(output_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "input_json": run_cfg.input_json,
                "external_val_json": run_cfg.external_val_json,
                "output_dir": run_cfg.output_dir,
                "text_field": run_cfg.text_field,
                "use_summary_header": run_cfg.use_summary_header,
                "split_mode": split_mode,
                "split": asdict(run_cfg.split),
                "train": asdict(run_cfg.train),
                "dataset_sizes": {
                    "train_source_all": int(len(train_source_df)),
                    "train": int(len(train_df)),
                    "val": int(len(val_df)),
                    "test": int(len(test_df)),
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    train_dataset = to_hf_dataset(train_df)
    val_dataset = to_hf_dataset(val_df)

    model = build_model(run_cfg.train)
    training_args = build_training_args(run_cfg.train)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        metric="accuracy",
        column_mapping={"text": "text", "label": "label"},
    )

    trainer.train(num_iterations=run_cfg.train.num_iterations)
    model.save_pretrained(output_dir / "model")

    train_metrics = evaluate_and_save(model, trainer, "train", train_df, output_dir)
    val_metrics = evaluate_and_save(model, trainer, "val", val_df, output_dir)
    test_metrics = evaluate_and_save(model, trainer, "test", test_df, output_dir)

    summary = {
        "recommended_metric": "val_macro_f1",
        "split_mode": split_mode,
        "train": train_metrics["extra_metrics"],
        "val": val_metrics["extra_metrics"],
        "test": test_metrics["extra_metrics"],
    }
    with open(output_dir / "summary_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Training complete.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
