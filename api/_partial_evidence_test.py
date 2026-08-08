from opportunity_evidence import build_opportunity_evidence

opportunity = {
    "type": "DOT_GAP",
    "ability_name": "Moonfire",
    "classification": "LIKELY_DOWNTIME",
    "confidence": "HIGH",
    "score": 85,
    "dot_evidence": {
        "_gap_start": 1000,
        "_gap_end": 5000,
        "target_count": 1,
        "temporal_coverage": {
            "123": {
                "coverage": "PARTIAL",
                "gap_seconds": 4,
                "coverage_seconds": 2,
                "coverage_ratio": 0.5,
                "active_at_gap_start": True,
                "active_at_gap_end": False,
                "open_at_end": False,
                "intervals": [[1000, 3000]],
            }
        },
        "target_diagnostics": {
            "123": {
                "final_state": "REMOVED_ONLY",
                "explained_by": "REMOVAL",
                "applied_during_gap": False,
                "refreshed_during_gap": False,
                "removed_during_gap": True,
                "stack_removals_during_gap": 0,
            }
        },
    },
}

evidence = build_opportunity_evidence(opportunity)

print("PARTIAL HIGH-SCORE TEST: PASS")
print("Strength:", evidence["evidence_strength"])
print("Coverage:", evidence["coverage"])
print("Final states:", evidence["final_states"])
print("Reason:", evidence["reason"])
