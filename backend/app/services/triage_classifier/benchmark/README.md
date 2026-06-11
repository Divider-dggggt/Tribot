# ATS Classification Benchmark

A focused benchmark and research experiment module for TRIBOT ATS
classification. It evaluates the existing ATS classification algorithms and
their rule-covered outputs using clinically meaningful **ordinal safety
metrics**, and provides optional research-only training/evaluation scripts
for ordinal DeBERTa and safety-cost-aware DeBERTa.

This module is **benchmark-only**: it reuses the existing production model
wrappers and rule engine without modifying them, and it does not change
production API behavior.

## ATS convention

- **ATS 1 is most urgent, ATS 5 is least urgent.** Smaller number = more urgent.
- **Under-triage**: `predicted_ats > gold_ats` (clinically dangerous).
- **Over-triage**: `predicted_ats < gold_ats` (resource cost).

## Models

| Model | Source | Notes |
| --- | --- | --- |
| `baseline` | `../baseline_predict.py` | TF-IDF + classical ML |
| `deberta` | `../sprint2_deberta_classifier.py` | Production DeBERTa classifier |
| `setfit` | `../sprint2_setfit_classifier.py` | Production SetFit classifier |
| `rag` | `../sprint3_rag.py` | **RAG + handbook ATS classification model** (handbook retrieval + LLM). It is an ATS *classifier*, not an audit module. |
| `ordinal_deberta` (optional) | `ordinal_deberta.py` | Research-only cumulative ordinal model |
| `safety_cost_deberta` (optional) | `safety_cost_deberta.py` | Research-only safety-cost-aware model |

The rule-based severity engine (`../severity_flagging.py`) is run once per
case as the safety coverage layer.

If a model fails for a sample (missing dependency, missing API key,
unreachable service, etc.), the error is recorded in `predictions.jsonl` /
`predictions.csv` and the benchmark continues with the remaining models.

## Rule coverage — Safety-Dominant Fusion Rule

The hybrid rule + model logic is treated as a formal algorithm. Given model
prediction `y_model` and rule prediction `y_rule`, the rule-covered
prediction is:

```
y_final = min(y_model, y_rule)
```

when both are valid. If only one is valid, that one is used; if neither is
valid, the output is `None`.

Since lower ATS values represent higher urgency, `y_final <= y_rule` and
`y_final <= y_model`. **Therefore, the final output cannot downgrade an
accepted safety signal** — it is never less urgent than the rule-based
recommendation. This fusion is applied only inside the benchmark output
calculation; production code is unchanged.

## Clinical severity energy function (benchmark-only)

The existing rule-based severity output is formalized, for interpretation
purposes only, as a clinical severity energy function:

```
E(x) = sum base_presentations + sum upward_modifiers
       - sum downward_modifiers + hard_override_bonus

rule_ats = g(E(x))
```

where **higher energy means greater clinical urgency**. `rule_energy.py`
derives this summary robustly from the fields exposed by
`flag_high_severity` (presentation scores, modifier matches, hard
overrides), with a simple fallback when explicit fields are unavailable. It
is an interpretation layer: it does not re-run or change rule logic, and is
not guaranteed to exactly reproduce internal rule arithmetic.

Each prediction row stores `rule_energy`, `rule_energy_components`, and
`rule_energy_explanation`.

## Metrics

Implemented in `metrics.py` (`compute_ats_metrics`):

- `num_cases`, `accuracy`, `macro_f1`, `weighted_f1`
- `per_class_precision`, `per_class_recall`, `per_class_f1`, `confusion_matrix`
- `under_triage_rate` — fraction of cases with `pred > gold`
- `over_triage_rate` — fraction of cases with `pred < gold`
- `exact_match_rate`, `adjacent_accuracy` (`abs(pred - gold) <= 1`)
- `mean_absolute_ordinal_error`
- `under_triage_severity_index` — `mean(max(0, pred - gold))`
- `squared_under_triage_severity_index` — `mean(max(0, pred - gold) ** 2)`
- `critical_under_triage_rate` — fraction with `gold in [1, 2] and pred >= 3`
- `ats_1_recall`, `ats_2_recall`, `ats_1_2_recall`
- `asymmetric_safety_cost_mean`
- `safety_weighted_accuracy`

### Asymmetric safety cost

```
cost(gold, pred) = 0                              if pred == gold
                 = lambda_under * (pred - gold)^2 if pred > gold  (under-triage)
                 = lambda_over * (gold - pred)    if pred < gold  (over-triage)
```

Defaults: `lambda_under = 5.0`, `lambda_over = 1.0` — under-triage is
penalized more heavily (and quadratically) because it is clinically more
dangerous.

### Safety-weighted accuracy (SWA)

```
swa = 1 - (mean_actual_cost / mean_max_possible_cost)
```

where for each gold label the maximum possible cost is computed across all
possible ATS predictions 1–5 with the same asymmetric cost function. The
final SWA is clamped into `[0, 1]`.

## How to run

From the project root
(`/home/ubuntu/test_proj/capstone-project-26t1-9900-w18c-donut`):

```bash
# Original validation scenarios
python -m backend.app.services.triage_classifier.benchmark.run_benchmark \
    --input scenarios.json \
    --output-dir benchmark_outputs/scenarios \
    --models baseline deberta setfit rag \
    --lambda-under 5 \
    --lambda-over 1

# Generated v3 sample
python -m backend.app.services.triage_classifier.benchmark.run_benchmark \
    --input generated_scenarios_v3.json \
    --output-dir benchmark_outputs/generated_v3_sample \
    --models baseline deberta setfit rag \
    --limit 100 \
    --lambda-under 5 \
    --lambda-over 1

# High-acuity generated sample
python -m backend.app.services.triage_classifier.benchmark.run_benchmark \
    --input generated_scenarios_5000.json \
    --output-dir benchmark_outputs/generated_5000_sample \
    --models baseline deberta setfit rag \
    --limit 100 \
    --lambda-under 5 \
    --lambda-over 1
```

Dataset paths are resolved against the current directory, the project root,
and the known dataset directory `/home/ubuntu/test`. Any JSON file whose
records contain at least `dialogue_text` and `ats_category` is supported
(field names configurable via `--text-field` / `--label-field`). The data
files themselves are never modified.

### CLI arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--input` | (required) | Path to JSON dataset |
| `--output-dir` | (required) | Output directory |
| `--models` | all four | Any of `baseline deberta setfit rag` |
| `--limit` | none | Optional integer case limit |
| `--lambda-under` | 5 | Under-triage cost weight |
| `--lambda-over` | 1 | Over-triage cost weight |
| `--text-field` | `dialogue_text` | Text field name |
| `--label-field` | `ats_category` | Gold label field name |
| `--include-soap-summary` | false | Also call the existing SOAP generator per case |
| `--include-ordinal-deberta` | false | Evaluate optional ordinal DeBERTa |
| `--ordinal-model-path` | none | Path to trained ordinal model |
| `--include-safety-cost-deberta` | false | Evaluate optional safety-cost DeBERTa |
| `--safety-cost-model-path` | none | Path to trained safety-cost model |

### Output files

- `predictions.jsonl`, `predictions.csv` — per-case predictions, errors,
  rule energy and (optional) SOAP summaries
- `metrics_summary.json`, `metrics_summary.md` — metrics per model
  (`*_raw` and `*_rule_covered` columns)
- `confusion_matrices.json` — confusion matrix per prediction column
- `benchmark_config.json` — full run configuration

## How to interpret the safety metrics

- **Under-triage rate**: how often the model assigns a *less* urgent
  category than gold. The key clinical risk metric — lower is better.
- **Over-triage rate**: how often the model assigns a *more* urgent
  category than gold. Mainly a resource-utilisation concern.
- **Critical under-triage rate**: gold ATS 1–2 cases predicted as ATS >= 3,
  i.e. truly time-critical patients pushed into non-urgent queues. This is
  the most safety-relevant single number.
- **Under-triage severity index**: average *depth* of under-triage in
  categories (0 when never under-triaging). The squared variant emphasises
  deep misses (e.g. gold ATS 1 predicted ATS 4).
- **Asymmetric safety cost**: a single ordinal score combining both error
  directions with under-triage weighted more heavily.
- **Safety-weighted accuracy**: normalized inverse cost in `[0, 1]`; 1.0
  means zero safety cost, 0.0 means worst possible predictions.

## Ordinal DeBERTa (research-only)

ATS is ordinal (`ATS 1 < ATS 2 < ... < ATS 5`, smaller = more urgent), not
an unordered 5-class task. `ordinal_deberta.py` implements the cumulative
ordinal formulation:

- For labels 1–5, create 4 binary targets `t_k = 1 if y <= k else 0`,
  `k = 1..4` (e.g. label 1 → `[1, 1, 1, 1]`, label 5 → `[0, 0, 0, 0]`).
- The model outputs **4 logits** `z_1..z_4` for **5 ATS categories**, with
  `P(y <= k | x) = sigmoid(z_k)`.
- Training loss: `L_ord = sum_k BCEWithLogitsLoss(z_k, t_k)`.
- Decoding: count how many cumulative thresholds are true; 4 true → ATS 1,
  3 → ATS 2, 2 → ATS 3, 1 → ATS 4, 0 → ATS 5.

Train explicitly (never run automatically by the benchmark):

```bash
python -c "
from backend.app.services.triage_classifier.benchmark.ordinal_deberta import train_ordinal_deberta
train_ordinal_deberta('/home/ubuntu/test/generated_scenarios_v3.json',
                      'backend/app/services/triage_classifier/models/deberta_ordinal_model')
"
```

Then evaluate inside the benchmark:

```bash
python -m backend.app.services.triage_classifier.benchmark.run_benchmark \
    --input scenarios.json \
    --output-dir benchmark_outputs/scenarios_with_ordinal \
    --models baseline deberta setfit rag \
    --include-ordinal-deberta \
    --ordinal-model-path backend/app/services/triage_classifier/models/deberta_ordinal_model \
    --lambda-under 5 \
    --lambda-over 1
```

If the model path is missing, a clear warning is recorded and the benchmark
continues without it.

## Safety-cost DeBERTa (research-only)

Ordinary multiclass cross-entropy treats all wrong labels too similarly; in
triage, **under-triage receives a larger penalty**. `safety_cost_deberta.py`
implements:

```
loss = CE + alpha * expected_safety_cost
expected_safety_cost = sum_k p_k * C(y, k)

C(y, k) = 0                          if k == y
        = lambda_under * (k - y)^2   if k > y   (under-triage)
        = lambda_over * (y - k)      if k < y   (over-triage)
```

Defaults: `alpha = 0.2`, `lambda_under = 5.0`, `lambda_over = 1.0`.

Train explicitly with `train_safety_cost_deberta(...)` (analogous to the
ordinal model above), then evaluate with `--include-safety-cost-deberta
--safety-cost-model-path PATH`.

Neither research model replaces the production DeBERTa classifier
(`sprint2_deberta_classifier.py`), and neither is trained automatically
during benchmark evaluation.

## Notes

- RAG is treated as an **ATS classification model using handbook
  retrieval**, not as an audit module. If RAG requires an API key or
  external service and fails, the benchmark still completes for baseline,
  DeBERTa, SetFit, rule, and rule-covered variants, recording RAG errors per
  case.
- Results are technical and preliminary; they do not establish clinical
  validity.
