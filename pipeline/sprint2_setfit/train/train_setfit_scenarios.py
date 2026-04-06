#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datasets import Dataset
from setfit import SetFitModel, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

LABELS = [1, 2, 3, 4, 5]
LABEL_TO_INDEX = {label: idx for idx, label in enumerate(LABELS)}
INDEX_TO_LABEL = {idx: label for label, idx in LABEL_TO_INDEX.items()}
REQUIRED_FIELDS = {"scenario_number", "scenario_summary_header", "dialogue_text", "ats_category"}


@dataclass
class SplitConfig:
    test_size: float = 0.15
    val_size: float = 0.15
    seed: int = 42
    group_by_header: bool = False


@dataclass
class TrainConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 128
    num_epochs: int = 4
    num_iterations: int = 20
    body_learning_rate: float = 2e-5
    max_length: int = 192
    use_amp: bool = True
    head_type: str = "logistic"
    end_to_end: bool = False
    head_learning_rate: float = 1e-2
    l2_weight: float = 0.0


@dataclass
class RunConfig:
    input_jsons: List[str]
    output_dir: str
    external_val_jsons: List[str] = field(default_factory=list)
    text_field: str = "dialogue_text"
    use_summary_header: bool = False
    include_ats_note_in_text: bool = False
    strip_conclusion_lines: bool = False
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
    parser = argparse.ArgumentParser(description="Train SetFit from scenario-format triage JSON files")
    parser.add_argument("--input_jsons", nargs="+", required=True, help="One or more scenario-format JSON files for train/test source")
    parser.add_argument("--external_val_jsons", nargs="*", default=[], help="Optional one or more scenario-format JSON files used only as external validation")
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
    parser.add_argument("--val_size", type=float, default=0.15)
    parser.add_argument("--text_field", type=str, default="dialogue_text")
    parser.add_argument("--use_summary_header", action="store_true")
    parser.add_argument("--include_ats_note_in_text", action="store_true", help="Not recommended for evaluation; can leak labels")
    parser.add_argument("--strip_conclusion_lines", action="store_true", help="Remove obvious nurse conclusion / routing lines from dialogue_text")
    parser.add_argument("--group_by_header", action="store_true", help="Split by normalized scenario_summary_header to reduce leakage")
    parser.add_argument("--no_amp", action="store_true")
    parser.add_argument("--head_type", choices=["logistic", "differentiable"], default="logistic")
    parser.add_argument("--end_to_end", action="store_true")
    return parser.parse_args()


def _coerce_label(value) -> int:
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, str):
        m = re.search(r"\b([1-5])\b", value)
        if m:
            return int(m.group(1))
    raise ValueError(f"Invalid ats_category: {value!r}")


def load_rows(input_json: str, source_name: Optional[str] = None) -> List[dict]:
    with open(input_json, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"{input_json}: expected a list of records")

    out = []
    source = source_name or Path(input_json).stem

    dropped_missing_label = 0
    dropped_bad_label = 0

    for i, row in enumerate(rows):
        missing = REQUIRED_FIELDS - set(row.keys())
        if missing:
            raise ValueError(f"{input_json} row {i} missing fields: {missing}")

        row = dict(row)
        row["source_file"] = source

        # 允许某些样本没标签；训练/验证时直接丢掉
        if "ats_category" not in row or row["ats_category"] in (None, "", "NA", "N/A"):
            dropped_missing_label += 1
            continue

        try:
            row["ats_category"] = _coerce_label(row["ats_category"])
        except Exception:
            dropped_bad_label += 1
            continue

        if row["ats_category"] not in LABEL_TO_INDEX:
            dropped_bad_label += 1
            continue

        out.append(row)

    print(
        f"[load_rows] {input_json}: kept={len(out)}, "
        f"dropped_missing_label={dropped_missing_label}, dropped_bad_label={dropped_bad_label}"
    )
    return out


def load_many(paths: List[str]) -> List[dict]:
    all_rows: List[dict] = []
    for p in paths:
        all_rows.extend(load_rows(p))
    return all_rows


def strip_obvious_conclusion_lines(text: str) -> str:
    bad_patterns = [
        r"we('ll| will) take you straight (through|to).*",
        r"we('re| are) taking you straight.*",
        r"no waiting room.*",
        r"you('?ll| will) be seen in .* area.*",
        r"this is non-urgent.*",
        r"lowest-acuity stream.*",
        r"priority seen urgently.*",
        r"we need to get you into (resus|the acute area|acute care).*",
        r"we('ll| will) bring you straight into.*",
    ]
    lines = [ln.strip() for ln in text.splitlines()]
    kept = []
    for line in lines:
        low = line.lower()
        if any(re.search(pat, low) for pat in bad_patterns):
            continue
        kept.append(line)
    return "\n".join([ln for ln in kept if ln]).strip()


def normalize_header_group(header: str) -> str:
    s = header.lower().strip()
    s = re.sub(r"\(ats[^)]*\)", "", s)
    parts = [p.strip() for p in s.split("-")]
    if len(parts) >= 2:
        s = " - ".join(parts[:-1]).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def build_text(row: dict, text_field: str, use_summary_header: bool, include_ats_note_in_text: bool, strip_conclusion_lines: bool) -> str:
    if text_field not in row:
        raise KeyError(f"text_field={text_field!r} not found in row")
    text = str(row[text_field]).strip()
    if strip_conclusion_lines:
        text = strip_obvious_conclusion_lines(text)
    if use_summary_header:
        header = str(row.get("scenario_summary_header", "")).strip()
        if header:
            text = f"{header}\n\n{text}"
    if include_ats_note_in_text:
        note = str(row.get("ats_note", "")).strip()
        if note:
            text = f"{text}\n\nATS Note: {note}"
    return text


def make_dataframe(rows: List[dict], cfg: RunConfig) -> pd.DataFrame:
    df = pd.DataFrame(rows).copy()
    df["text"] = [
        build_text(
            r,
            text_field=cfg.text_field,
            use_summary_header=cfg.use_summary_header,
            include_ats_note_in_text=cfg.include_ats_note_in_text,
            strip_conclusion_lines=cfg.strip_conclusion_lines,
        )
        for r in rows
    ]
    df["label"] = df["ats_category"].map(LABEL_TO_INDEX).astype(int)
    df["group"] = df["scenario_summary_header"].map(normalize_header_group)
    keep_cols = [
        "source_file",
        "scenario_number",
        "scenario_summary_header",
        "dialogue_text",
        "ats_category",
        "text",
        "label",
        "group",
    ]
    if "ats_note" in df.columns:
        keep_cols.insert(5, "ats_note")
    return df[keep_cols]


def plain_stratified_split(df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df, test_df = train_test_split(
        df, test_size=cfg.test_size, stratify=df["label"], random_state=cfg.seed
    )
    rel_val = cfg.val_size / (1.0 - cfg.test_size)
    train_df, val_df = train_test_split(
        train_df, test_size=rel_val, stratify=train_df["label"], random_state=cfg.seed
    )
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def group_split(df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gss = GroupShuffleSplit(n_splits=1, test_size=cfg.test_size, random_state=cfg.seed)
    train_idx, test_idx = next(gss.split(df, groups=df["group"]))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    rel_val = cfg.val_size / (1.0 - cfg.test_size)
    gss2 = GroupShuffleSplit(n_splits=1, test_size=rel_val, random_state=cfg.seed)
    tr_idx, val_idx = next(gss2.split(train_df, groups=train_df["group"]))
    final_train = train_df.iloc[tr_idx].reset_index(drop=True)
    val_df = train_df.iloc[val_idx].reset_index(drop=True)
    return final_train, val_df, test_df


def split_with_external_val(train_source_df: pd.DataFrame, external_val_df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if cfg.group_by_header:
        gss = GroupShuffleSplit(n_splits=1, test_size=cfg.test_size, random_state=cfg.seed)
        train_idx, test_idx = next(gss.split(train_source_df, groups=train_source_df["group"]))
        train_df = train_source_df.iloc[train_idx].reset_index(drop=True)
        test_df = train_source_df.iloc[test_idx].reset_index(drop=True)
    else:
        train_df, test_df = train_test_split(
            train_source_df,
            test_size=cfg.test_size,
            stratify=train_source_df["label"],
            random_state=cfg.seed,
        )
        train_df = train_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)
    return train_df, external_val_df.reset_index(drop=True), test_df


def to_hf_dataset(df: pd.DataFrame) -> Dataset:
    return Dataset.from_pandas(df[["text", "label"]], preserve_index=False)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true_ats = np.vectorize(INDEX_TO_LABEL.get)(y_true)
    y_pred_ats = np.vectorize(INDEX_TO_LABEL.get)(y_pred)
    under = float(np.mean(y_pred_ats > y_true_ats))
    over = float(np.mean(y_pred_ats < y_true_ats))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "under_triage_rate": under,
        "over_triage_rate": over,
    }


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


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
    thresh = cm.max() / 2.0 if cm.max() > 0 else 0.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def evaluate_split(model: SetFitModel, df: pd.DataFrame, split_name: str, output_dir: Path) -> Dict[str, float]:
    y_true = df["label"].to_numpy()
    y_pred = np.asarray(model.predict(df["text"].tolist()))
    metrics = compute_metrics(y_true, y_pred)
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=[str(x) for x in LABELS],
        output_dict=True,
        zero_division=0,
    )

    pred_df = df.copy()
    pred_df["pred_label_idx"] = y_pred
    pred_df["pred_ats"] = [INDEX_TO_LABEL[int(x)] for x in y_pred]
    pred_df["true_ats"] = [INDEX_TO_LABEL[int(x)] for x in y_true]
    pred_df.to_csv(output_dir / f"{split_name}_predictions.csv", index=False)

    save_json(metrics, output_dir / f"{split_name}_metrics.json")
    save_json(report, output_dir / f"{split_name}_classification_report.json")
    plot_confusion(y_true, y_pred, output_dir / f"{split_name}_confusion.png")
    return metrics


def main() -> None:
    args = parse_args()
    run_cfg = RunConfig(
        input_jsons=args.input_jsons,
        external_val_jsons=args.external_val_jsons,
        output_dir=args.output_dir,
        text_field=args.text_field,
        use_summary_header=args.use_summary_header,
        include_ats_note_in_text=args.include_ats_note_in_text,
        strip_conclusion_lines=args.strip_conclusion_lines,
        split=SplitConfig(
            test_size=args.test_size,
            val_size=args.val_size,
            seed=args.seed,
            group_by_header=args.group_by_header,
        ),
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

    set_seed(run_cfg.split.seed)
    out_dir = Path(run_cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_rows = load_many(run_cfg.input_jsons)
    train_source_df = make_dataframe(train_rows, run_cfg)

    if run_cfg.external_val_jsons:
        external_rows = load_many(run_cfg.external_val_jsons)
        external_val_df = make_dataframe(external_rows, run_cfg)
        train_df, val_df, test_df = split_with_external_val(train_source_df, external_val_df, run_cfg.split)
    else:
        if run_cfg.split.group_by_header:
            train_df, val_df, test_df = group_split(train_source_df, run_cfg.split)
        else:
            train_df, val_df, test_df = plain_stratified_split(train_source_df, run_cfg.split)

    train_df.to_json(out_dir / "train_split.json", orient="records", force_ascii=False, indent=2)
    val_df.to_json(out_dir / "val_split.json", orient="records", force_ascii=False, indent=2)
    test_df.to_json(out_dir / "test_split.json", orient="records", force_ascii=False, indent=2)

    if run_cfg.train.head_type == "differentiable":
        model = SetFitModel.from_pretrained(
            run_cfg.train.model_name,
            use_differentiable_head=True,
            head_params={"out_features": len(LABELS)},
        )
    else:
        model = SetFitModel.from_pretrained(
            run_cfg.train.model_name,
            use_differentiable_head=False,
        )
        train_ds = to_hf_dataset(train_df)
        val_ds = to_hf_dataset(val_df)

    train_args = TrainingArguments(
        batch_size=128,
        num_epochs=4,
        max_steps=800,
        body_learning_rate=run_cfg.train.body_learning_rate,
        head_learning_rate=run_cfg.train.head_learning_rate,
        l2_weight=run_cfg.train.l2_weight,
        max_length=192,
        use_amp=run_cfg.train.use_amp,
        output_dir=str(out_dir / "trainer_output"),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="embedding_loss",
        greater_is_better=False,
        seed=run_cfg.split.seed,
    )

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    trainer.train()

    model_dir = out_dir / "final_model"
    model.save_pretrained(str(model_dir))

    metrics = {
        "recommended_metric": "val_macro_f1",
        "train": evaluate_split(model, train_df, "train", out_dir),
        "val": evaluate_split(model, val_df, "val", out_dir),
        "test": evaluate_split(model, test_df, "test", out_dir),
    }
    save_json(metrics, out_dir / "summary_metrics.json")
    save_json(
        {
            "input_jsons": run_cfg.input_jsons,
            "external_val_jsons": run_cfg.external_val_jsons,
            "use_summary_header": run_cfg.use_summary_header,
            "include_ats_note_in_text": run_cfg.include_ats_note_in_text,
            "strip_conclusion_lines": run_cfg.strip_conclusion_lines,
            "group_by_header": run_cfg.split.group_by_header,
            "seed": run_cfg.split.seed,
            "model_name": run_cfg.train.model_name,
        },
        out_dir / "run_config_used.json",
    )

    print("Training complete.")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()