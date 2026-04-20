from __future__ import annotations

import json
import re
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence

from .handbook_index import HandbookIndex
from .soap_parsing import flatten_prediction, validate_prediction_structure
from .text_utils import MatchResult, TextMatcher


SECTION_THRESHOLD = 0.55
ANY_SECTION_THRESHOLD = 0.60
SUPPORTED_THRESHOLD = 0.55


def _extract_numberish(text: str) -> List[str]:
    return re.findall(r"\b\d+(?:\.\d+)?(?:/\d+)?%?\b", str(text))


def _urgency_expected(gold_record: Dict[str, Any]) -> bool:
    cat = gold_record.get("ats_category")
    return int(cat) in {1, 2}


def _contains_urgency_language(texts: Sequence[str]) -> bool:
    blob = " ".join(texts).lower()
    return any(x in blob for x in ["urgent", "straight through", "acute area", "acute care", "resus", "no waiting"])


def _detect_negation_flip(gold_facts: Sequence[Dict[str, Any]], pred_facts: Sequence[Dict[str, str]]) -> List[str]:
    errors: List[str] = []
    pred_blob = " ".join(x["content"] for x in pred_facts).lower()
    for fact in gold_facts:
        if fact.get("polarity") != "negative":
            continue
        gold_text = fact["content"].lower()
        if gold_text.startswith(("no ", "not ", "never ")):
            target = re.sub(r"^(no|not|never)\s+", "", gold_text).strip()
            if target and target in pred_blob and "no " + target not in pred_blob and "not " + target not in pred_blob:
                errors.append(f"possible negation flip: {fact['content']}")
    return errors


def _detect_number_mismatch(gold_facts: Sequence[Dict[str, Any]], pred_facts: Sequence[Dict[str, str]]) -> List[str]:
    errors: List[str] = []
    pred_blob = " ".join(x["content"] for x in pred_facts)
    for fact in gold_facts:
        nums = _extract_numberish(fact["content"])
        if not nums:
            continue
        for num in nums:
            if num not in pred_blob and fact.get("must_include") and fact["section_gold"] in {"objective", "assessment"}:
                errors.append(f"missing expected numeric detail: {fact['content']}")
                break
    return errors


def _handbook_alignment_score(handbook: HandbookIndex, gold_record: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, Any]:
    soap = pred.get("soap", {}) or {}
    assessment = soap.get("assessment", []) or []
    plan = soap.get("plan", []) or []
    query = " ".join([
        gold_record.get("summary_header", ""),
        gold_record.get("ats_note", ""),
        " ".join(gold_record.get("gold_soap", {}).get("assessment", [])),
        " ".join(gold_record.get("gold_soap", {}).get("plan", [])),
    ]).strip()
    retrieved = handbook.search(query, top_k=5)
    source_texts = [x["text"] for x in retrieved]
    candidate = " ".join([*(assessment if isinstance(assessment, list) else []), *(plan if isinstance(plan, list) else [])]).strip()
    if not candidate or not source_texts:
        return {"score": 0.0, "retrieved": retrieved}
    matcher = TextMatcher(source_texts)
    best = matcher.best_match(candidate, source_texts)
    return {"score": float(best.score), "retrieved": retrieved}


def evaluate_single_prediction(gold_record: Dict[str, Any], pred: Dict[str, Any], handbook: Optional[HandbookIndex] = None) -> Dict[str, Any]:
    structure = validate_prediction_structure(pred)
    structure_score = 1.0 if structure["valid"] else 0.0

    pred_facts = flatten_prediction(pred)
    gold_facts = gold_record["facts"]

    pred_by_section = defaultdict(list)
    for f in pred_facts:
        pred_by_section[f["section_pred"]].append(f["content"])
    all_pred_texts = [f["content"] for f in pred_facts]

    matched_gold = []
    must_total = sum(1 for f in gold_facts if f["must_include"])
    must_hit = 0

    for gold_fact in gold_facts:
        section = gold_fact["section_gold"]
        same_section = pred_by_section.get(section, [])
        best_same = TextMatcher(same_section).best_match(gold_fact["content"], same_section) if same_section else MatchResult(0.0, -1, "")
        best_any = TextMatcher(all_pred_texts).best_match(gold_fact["content"], all_pred_texts) if all_pred_texts else MatchResult(0.0, -1, "")

        covered = best_same.score >= SECTION_THRESHOLD
        covered_any = best_any.score >= ANY_SECTION_THRESHOLD

        matched_gold.append({
            "fact_id": gold_fact["fact_id"],
            "gold_text": gold_fact["content"],
            "section_gold": section,
            "best_same_score": best_same.score,
            "best_same_text": best_same.text,
            "best_any_score": best_any.score,
            "best_any_text": best_any.text,
            "covered": covered,
            "covered_any": covered_any,
            "must_include": gold_fact["must_include"],
        })
        if gold_fact["must_include"] and covered:
            must_hit += 1

    must_fact_recall = must_hit / must_total if must_total else 0.0

    unmatched_pred = 0
    pred_matches = []
    gold_texts = [f["content"] for f in gold_facts]
    gold_matcher = TextMatcher(gold_texts)
    for pf in pred_facts:
        best = gold_matcher.best_match(pf["content"], gold_texts) if gold_texts else MatchResult(0.0, -1, "")
        pred_matches.append({"pred_text": pf["content"], "section_pred": pf["section_pred"], "best_gold_score": best.score, "best_gold_text": best.text})
        if best.score < SUPPORTED_THRESHOLD:
            unmatched_pred += 1

    supported_precision = 1.0 - (unmatched_pred / len(pred_facts)) if pred_facts else 0.0

    matched_any = [m for m in matched_gold if m["covered_any"]]
    placed_correct = [m for m in matched_gold if m["covered"]]
    section_placement = len(placed_correct) / len(matched_any) if matched_any else 0.0

    soap = pred.get("soap", {}) or {}
    subj = soap.get("subjective", {}) or {}
    obj = soap.get("objective", {}) or {}
    assessment_ok = 1.0 if (soap.get("assessment") and len(soap.get("assessment")) > 0) else 0.0
    plan_ok = 1.0 if (soap.get("plan") and len(soap.get("plan")) > 0) else 0.0
    section_nonempty = (
        int(bool(subj.get("chief_complaint")))
        + int(bool(subj.get("history_of_present_illness")))
        + int(bool(obj.get("exam_findings") or obj.get("vitals")))
        + int(assessment_ok > 0)
        + int(plan_ok > 0)
    )
    clinical_adequacy = min(1.0, 0.25 * assessment_ok + 0.25 * plan_ok + 0.25 * (section_nonempty / 5.0) + 0.25 * must_fact_recall)

    critical_errors: List[str] = []
    critical_errors.extend(_detect_negation_flip(gold_facts, pred_facts))
    critical_errors.extend(_detect_number_mismatch(gold_facts, pred_facts))

    if _urgency_expected(gold_record):
        pred_plan = soap.get("plan", []) or []
        if not _contains_urgency_language([str(x) for x in pred_plan]):
            critical_errors.append("urgency / disposition language missing for ATS 1-2 case")

    safety_penalty = min(1.0, 0.15 * len(critical_errors))
    safety_score = max(0.0, 1.0 - safety_penalty)

    handbook_result = None
    handbook_score = None
    if handbook is not None:
        handbook_result = _handbook_alignment_score(handbook=handbook, gold_record=gold_record, pred=pred)
        handbook_score = handbook_result["score"]

    total_score = (
        0.10 * structure_score
        + 0.30 * must_fact_recall
        + 0.20 * supported_precision
        + 0.15 * section_placement
        + 0.15 * clinical_adequacy
        + 0.10 * safety_score
    )

    return {
        "scenario_number": gold_record["scenario_number"],
        "structure_score": round(structure_score, 4),
        "must_fact_recall": round(must_fact_recall, 4),
        "supported_precision": round(supported_precision, 4),
        "section_placement": round(section_placement, 4),
        "clinical_adequacy": round(clinical_adequacy, 4),
        "safety_score": round(safety_score, 4),
        "critical_errors": critical_errors,
        "handbook_alignment": round(handbook_score, 4) if handbook_score is not None else None,
        "total_score": round(total_score, 4),
        "structure_errors": structure["errors"],
        "matched_gold": matched_gold,
        "pred_matches": pred_matches,
        "handbook_retrieval": handbook_result["retrieved"] if handbook_result else None,
    }


def _load_predictions(path: str) -> Dict[str, Dict[str, Any]]:
    data = json.loads(open(path, "r", encoding="utf-8").read())
    if isinstance(data, dict):
        if "scenario_number" in data:
            return {str(data["scenario_number"]): data}
        return {str(k): v for k, v in data.items()}
    if isinstance(data, list):
        return {str(item["scenario_number"]): item for item in data}
    raise ValueError("Unsupported prediction format.")


def evaluate_predictions(gold_path: str, pred_path: str, handbook_dir: Optional[str] = None, challenge_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    gold = json.loads(open(gold_path, "r", encoding="utf-8").read())
    preds = _load_predictions(pred_path)
    handbook = HandbookIndex(handbook_dir) if handbook_dir else None

    if challenge_ids is not None:
        gold = [x for x in gold if x["scenario_number"] in set(challenge_ids)]

    per_case = []
    for record in gold:
        sid = record["scenario_number"]
        pred = preds.get(sid)
        if pred is None:
            per_case.append({
                "scenario_number": sid,
                "missing_prediction": True,
                "structure_score": 0.0,
                "must_fact_recall": 0.0,
                "supported_precision": 0.0,
                "section_placement": 0.0,
                "clinical_adequacy": 0.0,
                "safety_score": 0.0,
                "critical_errors": ["missing prediction"],
                "handbook_alignment": None,
                "total_score": 0.0,
            })
            continue
        per_case.append(evaluate_single_prediction(record, pred, handbook=handbook))

    metrics = ["structure_score", "must_fact_recall", "supported_precision", "section_placement", "clinical_adequacy", "safety_score", "total_score"]
    summary = {m: round(mean([x[m] for x in per_case]), 4) if per_case else 0.0 for m in metrics}

    handbook_vals = [x["handbook_alignment"] for x in per_case if x.get("handbook_alignment") is not None]
    summary["handbook_alignment"] = round(mean(handbook_vals), 4) if handbook_vals else None
    summary["num_cases"] = len(per_case)
    summary["num_missing_predictions"] = sum(1 for x in per_case if x.get("missing_prediction"))
    summary["num_cases_with_critical_errors"] = sum(1 for x in per_case if x.get("critical_errors"))
    return {"summary": summary, "per_case": per_case}
