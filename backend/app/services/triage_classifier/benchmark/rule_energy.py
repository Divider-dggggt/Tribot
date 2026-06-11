"""Benchmark-only formalization of the rule-based severity output as a
clinical severity energy function.

Conceptual formula (documentation-level, see README):

    E(x) = sum base_presentations + sum upward_modifiers
           - sum downward_modifiers + hard_override_bonus

    rule_ats = g(E(x))

where higher energy means greater clinical urgency.

This module only *interprets* the output of the existing production rule
engine (`severity_flagging.flag_high_severity`). It never re-runs or
modifies rule logic, and the energy score is an interpretable approximation
rather than an exact reconstruction of internal rule internals.
"""

from __future__ import annotations

from .metrics import normalize_ats


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _override_bonus(override: dict) -> float:
    """Bonus energy for a hard override; more urgent override ATS -> more energy."""
    try:
        ats = normalize_ats(override.get("ats"))
    except (ValueError, TypeError):
        return 1.0
    return float(6 - ats)


def compute_rule_energy_from_result(severity_result: dict) -> dict:
    """Convert a `flag_high_severity(text)` result into an energy summary.

    Robust to missing fields: when explicit presentation scores or modifier
    details are unavailable, a simple fallback energy is derived from
    whatever fields exist (severity flags, recommended ATS, counts of
    matches/explanations). Never raises on missing fields.

    Returns:
        {
            "rule_ats": int | None,
            "severity_energy": float | None,
            "energy_components": {
                "base_presentations": float,
                "upward_modifiers": float,
                "downward_modifiers": float,
                "hard_overrides": float,
                "fallback_flags": float,
            },
            "explanation": "...",
        }
    """
    components = {
        "base_presentations": 0.0,
        "upward_modifiers": 0.0,
        "downward_modifiers": 0.0,
        "hard_overrides": 0.0,
        "fallback_flags": 0.0,
    }

    if not isinstance(severity_result, dict):
        return {
            "rule_ats": None,
            "severity_energy": None,
            "energy_components": components,
            "explanation": "No rule severity result available; energy not computed.",
        }

    rule_ats = None
    try:
        recommended = severity_result.get("recommended_ats_category")
        if recommended is not None:
            rule_ats = normalize_ats(recommended)
    except (ValueError, TypeError):
        rule_ats = None

    explanation_parts: list[str] = []

    presentations = severity_result.get("presentations")
    used_explicit_fields = False

    if isinstance(presentations, dict) and presentations:
        used_explicit_fields = True
        for name, data in presentations.items():
            if not isinstance(data, dict):
                continue
            score = _safe_float(data.get("score"))
            up_groups = data.get("upward_modifiers")
            down_groups = data.get("downward_modifiers")
            n_up = len(up_groups) if isinstance(up_groups, dict) else 0
            n_down = len(down_groups) if isinstance(down_groups, dict) else 0

            if score is not None:
                # The engine's per-presentation score already nets base and
                # modifier contributions; approximate the base part by
                # removing one energy unit per matched modifier group.
                base_part = max(0.0, score - float(n_up) + float(n_down))
                components["base_presentations"] += base_part
            components["upward_modifiers"] += float(n_up)
            components["downward_modifiers"] += float(n_down)

            detail = f"{name} (score={score if score is not None else 'n/a'}"
            if n_up:
                detail += f", +{n_up} upward"
            if n_down:
                detail += f", -{n_down} downward"
            detail += ")"
            explanation_parts.append(detail)

    overrides = severity_result.get("overrides")
    if isinstance(overrides, list) and overrides:
        used_explicit_fields = True
        for override in overrides:
            if isinstance(override, dict):
                bonus = _override_bonus(override)
                components["hard_overrides"] += bonus
                explanation_parts.append(
                    f"hard override {override.get('name', 'unknown')} (+{bonus:g})"
                )

    if not used_explicit_fields:
        # Fallback: derive a simple energy from whatever fields are present.
        fallback = 0.0
        if severity_result.get("is_high_severity"):
            fallback += 1.0
            explanation_parts.append("high-severity flag present (+1)")
        if rule_ats is not None:
            # More urgent recommendation -> more energy.
            fallback += float(6 - rule_ats)
            explanation_parts.append(f"recommended ATS {rule_ats} (+{6 - rule_ats})")
        notes = severity_result.get("severity_flag_notes")
        if isinstance(notes, str) and notes.strip() and "no severity flags" not in notes.lower():
            n_reasons = len([p for p in notes.split("|") if p.strip()])
            fallback += 0.5 * n_reasons
            explanation_parts.append(f"{n_reasons} note section(s) (+{0.5 * n_reasons:g})")
        components["fallback_flags"] = fallback

    severity_energy = (
        components["base_presentations"]
        + components["upward_modifiers"]
        - components["downward_modifiers"]
        + components["hard_overrides"]
        + components["fallback_flags"]
    )

    if explanation_parts:
        explanation = (
            "E(x) = base + upward - downward + override_bonus"
            + (" (fallback-derived)" if not used_explicit_fields else "")
            + f" = {severity_energy:g}. Contributions: "
            + "; ".join(explanation_parts)
            + ". Higher energy means greater clinical urgency."
        )
    else:
        explanation = "No severity flags detected; energy is 0."

    return {
        "rule_ats": rule_ats,
        "severity_energy": float(severity_energy),
        "energy_components": components,
        "explanation": explanation,
    }
