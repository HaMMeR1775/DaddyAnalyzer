"""Opportunity Evidence Layer.

Consumes the frozen opportunity_detector V12 output and converts each
opportunity into a stable, explainable evidence structure.

This module is intentionally read-only with respect to detector logic:
it does not change V12 scoring or target-state calculations.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


EVIDENCE_VERSION = "1.0"

# Evidence strengths are intentionally descriptive rather than claims of
# player error.
STRENGTHS = {"NONE", "LOW", "MEDIUM", "HIGH"}
COVERAGE_STATES = {"FULL", "PARTIAL", "NONE", "UNKNOWN"}
FINAL_STATES = {
    "REMOVED_ONLY",
    "ACTIVE_REESTABLISHED",
    "ACTIVE_REFRESHED",
    "ACTIVE_APPLIED",
    "ACTIVE_UNCHANGED",
    "ACTIVE",
    "INACTIVE",
    "UNKNOWN",
}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _normalize_strength(value: Any) -> str:
    value = str(value or "LOW").upper()
    return value if value in STRENGTHS else "LOW"


def _normalize_coverage(value: Any) -> str:
    value = str(value or "UNKNOWN").upper()
    return value if value in COVERAGE_STATES else "UNKNOWN"


def _normalize_final_state(value: Any) -> str:
    value = str(value or "UNKNOWN").upper()
    return value if value in FINAL_STATES else "UNKNOWN"


def _get_dot_evidence(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """Return the V12 DoT evidence payload without assuming one key name."""
    for key in ("dot_evidence", "target_state", "evidence"):
        value = opportunity.get(key)
        if isinstance(value, dict):
            # V12 target-state evidence is recognizable by these fields.
            if any(
                field in value
                for field in (
                    "temporal_coverage",
                    "target_diagnostics",
                    "active_targets_before_gap",
                    "final_state_summary",
                )
            ):
                return value
    return {}


def _coverage_records(dot_evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    temporal = dot_evidence.get("temporal_coverage") or {}
    diagnostics = dot_evidence.get("target_diagnostics") or {}

    records: List[Dict[str, Any]] = []

    if isinstance(temporal, dict):
        for target_key, data in temporal.items():
            if not isinstance(data, dict):
                continue

            diagnostic = diagnostics.get(target_key, {})
            if not isinstance(diagnostic, dict):
                diagnostic = {}

            coverage = _normalize_coverage(data.get("coverage"))
            gap_seconds = _as_float(
                data.get("gap_seconds"),
                _as_float(dot_evidence.get("_gap_end"), 0.0)
                - _as_float(dot_evidence.get("_gap_start"), 0.0),
            )
            coverage_seconds = _as_float(data.get("coverage_seconds"))
            ratio = data.get("coverage_ratio")

            if ratio is None:
                ratio = (
                    coverage_seconds / gap_seconds
                    if gap_seconds > 0
                    else 0.0
                )

            intervals = data.get("intervals") or data.get("observable_intervals") or []

            records.append(
                {
                    "target_id": target_key,
                    "coverage": coverage,
                    "coverage_seconds": round(max(0.0, coverage_seconds), 3),
                    "coverage_ratio": round(_clamp(_as_float(ratio)), 4),
                    "gap_seconds": round(max(0.0, gap_seconds), 3),
                    "active_at_gap_start": bool(
                        data.get(
                            "active_at_gap_start",
                            diagnostic.get("active_before_gap", False),
                        )
                    ),
                    "active_at_gap_end": bool(
                        data.get(
                            "active_at_gap_end",
                            data.get("open_at_end", False),
                        )
                    ),
                    "open_at_end": bool(data.get("open_at_end", False)),
                    "final_state": _normalize_final_state(
                        diagnostic.get(
                            "final_state",
                            data.get("final_state", "UNKNOWN"),
                        )
                    ),
                    "explained_by": str(
                        diagnostic.get("explained_by", "UNKNOWN")
                    ),
                    "applied_during_gap": bool(
                        diagnostic.get("applied_during_gap", False)
                    ),
                    "refreshed_during_gap": bool(
                        diagnostic.get("refreshed_during_gap", False)
                    ),
                    "removed_during_gap": bool(
                        diagnostic.get("removed_during_gap", False)
                    ),
                    "stack_removals_during_gap": _as_int(
                        diagnostic.get("stack_removals_during_gap", 0)
                    ),
                    "intervals": intervals,
                }
            )

    return sorted(
        records,
        key=lambda item: str(item["target_id"]),
    )


def _derive_coverage_summary(records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    summary = {state.lower(): 0 for state in COVERAGE_STATES}
    for record in records:
        summary[record["coverage"].lower()] += 1
    return summary


def _derive_final_state_summary(
    records: Iterable[Dict[str, Any]],
    dot_evidence: Dict[str, Any],
) -> Dict[str, int]:
    existing = dot_evidence.get("final_state_summary")
    if isinstance(existing, dict):
        normalized = {}
        for key, value in existing.items():
            normalized[_normalize_final_state(key)] = _as_int(value)
        return normalized

    summary: Dict[str, int] = {}
    for record in records:
        state = record["final_state"]
        summary[state] = summary.get(state, 0) + 1
    return summary


def _classify_evidence_strength(
    *,
    classification: str,
    confidence: str,
    score: int,
    records: List[Dict[str, Any]],
    dot_evidence: Dict[str, Any],
) -> str:
    """Translate detector evidence into evidence strength, not blame."""
    confidence = _normalize_strength(confidence)

    if not records:
        return "LOW"

    full = sum(r["coverage"] == "FULL" for r in records)
    partial = sum(r["coverage"] == "PARTIAL" for r in records)
    unknown = sum(r["coverage"] == "UNKNOWN" for r in records)
    none = sum(r["coverage"] == "NONE" for r in records)

    reestablished = sum(
        r["final_state"] == "ACTIVE_REESTABLISHED" for r in records
    )
    removed_only = sum(
        r["final_state"] == "REMOVED_ONLY" for r in records
    )

    if full == len(records):
        return "LOW"

    if (
        partial > 0
        and unknown == 0
        and reestablished == 0
        and score >= 70
    ):
        return "HIGH"

    if reestablished > 0 or unknown > 0:
        return "MEDIUM"

    if none > 0 and partial > 0:
        return "HIGH" if score >= 75 else "MEDIUM"

    if removed_only == len(records):
        return "LOW"

    return confidence


def _build_reason(
    *,
    classification: str,
    records: List[Dict[str, Any]],
    dot_evidence: Dict[str, Any],
) -> str:
    if not records:
        return (
            "Target-aware evidence was not available for this opportunity; "
            "no player mistake is inferred."
        )

    summary = _derive_coverage_summary(records)
    final_states = _derive_final_state_summary(records, dot_evidence)

    full = summary["full"]
    partial = summary["partial"]
    unknown = summary["unknown"]
    none = summary["none"]

    if full == len(records):
        return (
            "All observed target coverage spans the complete gap. "
            "The interval is therefore supported as likely normal."
        )

    if partial > 0:
        return (
            f"{partial} target(s) have only partial observable coverage, "
            f"while {unknown} remain open/unknown and {none} have no "
            "observable coverage. This supports a potential uptime issue, "
            "but does not by itself prove a gameplay mistake."
        )

    if unknown > 0:
        return (
            f"{unknown} target(s) remain open-ended in the observable data. "
            "Expiration cannot be inferred without additional aura-state "
            "evidence, so this remains a potential issue rather than a "
            "confirmed miss."
        )

    if final_states.get("ACTIVE_REESTABLISHED", 0) > 0:
        return (
            "A target was removed and subsequently re-established during "
            "the gap. Removal alone therefore does not explain the full "
            "interval; temporal coverage is the deciding evidence."
        )

    if none == len(records):
        return (
            "No observable DoT coverage was found for the active targets "
            "during the gap. This is strong evidence of a potential uptime "
            "loss, subject to the limits of the available aura events."
        )

    return (
        f"Observed target evidence supports classification "
        f"{classification}, but does not establish player error."
    )


def build_opportunity_evidence(
    opportunity: Dict[str, Any],
) -> Dict[str, Any]:
    """Build one stable evidence object from one V12 opportunity."""
    dot_evidence = _get_dot_evidence(opportunity)
    records = _coverage_records(dot_evidence)

    classification = str(
        opportunity.get("classification", "UNKNOWN")
    )
    confidence = _normalize_strength(
        opportunity.get("confidence", "LOW")
    )
    score = _as_int(opportunity.get("score", 0))

    strength = _classify_evidence_strength(
        classification=classification,
        confidence=confidence,
        score=score,
        records=records,
        dot_evidence=dot_evidence,
    )

    gap_start = dot_evidence.get("_gap_start")
    gap_end = dot_evidence.get("_gap_end")

    evidence = {
        "evidence_version": EVIDENCE_VERSION,
        "type": str(opportunity.get("type", "UNKNOWN")),
        "ability": str(
            opportunity.get(
                "ability_name",
                opportunity.get("name", "UNKNOWN"),
            )
        ),
        "classification": classification,
        "confidence": confidence,
        "evidence_strength": strength,
        "score": score,
        "time": {
            "start": gap_start,
            "end": gap_end,
            "duration_seconds": round(
                max(
                    0.0,
                    _as_float(gap_end) - _as_float(gap_start),
                ),
                3,
            ) if gap_start is not None and gap_end is not None else None,
        },
        "summary": {
            "targets": _as_int(dot_evidence.get("target_count")),
            "active_targets_before_gap": len(
                dot_evidence.get("active_targets_before_gap", []) or []
            ),
            "targets_during_gap": len(
                dot_evidence.get("targets_during_gap", []) or []
            ),
            "applications": _as_int(
                dot_evidence.get("applications_during_gap")
            ),
            "refreshes": _as_int(
                dot_evidence.get("refreshes_during_gap")
            ),
            "removals": _as_int(
                dot_evidence.get("removals_during_gap")
            ),
            "stack_removals": _as_int(
                dot_evidence.get("stack_removals_during_gap")
            ),
        },
        "coverage": _derive_coverage_summary(records),
        "final_states": _derive_final_state_summary(
            records,
            dot_evidence,
        ),
        "targets": records,
        "reason": _build_reason(
            classification=classification,
            records=records,
            dot_evidence=dot_evidence,
        ),
        "limitations": [
            "Evidence describes observable combat data, not player intent.",
            "UNKNOWN coverage does not imply that the DoT expired.",
            "No fixed DoT duration is assumed by this layer.",
            "Stack removal is not treated as full aura removal.",
        ],
    }

    return evidence


def build_opportunity_evidence_list(
    opportunities: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build evidence objects for a sequence of detector opportunities."""
    return [
        build_opportunity_evidence(opportunity)
        for opportunity in opportunities
        if isinstance(opportunity, dict)
    ]


def summarize_evidence(
    evidence_items: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return compact aggregate evidence statistics for an API response."""
    items = list(evidence_items)

    summary = {
        "evidence_version": EVIDENCE_VERSION,
        "opportunities": len(items),
        "by_strength": {strength: 0 for strength in STRENGTHS},
        "by_coverage": {state: 0 for state in COVERAGE_STATES},
        "by_classification": {},
    }

    for item in items:
        strength = _normalize_strength(
            item.get("evidence_strength")
        )
        summary["by_strength"][strength] += 1

        for state, count in (item.get("coverage") or {}).items():
            normalized = _normalize_coverage(state)
            summary["by_coverage"][normalized] += _as_int(count)

        classification = str(
            item.get("classification", "UNKNOWN")
        )
        summary["by_classification"][classification] = (
            summary["by_classification"].get(classification, 0) + 1
        )

    return summary


__all__ = [
    "EVIDENCE_VERSION",
    "build_opportunity_evidence",
    "build_opportunity_evidence_list",
    "summarize_evidence",
]
