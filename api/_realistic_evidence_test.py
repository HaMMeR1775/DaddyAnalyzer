from opportunity_evidence import build_opportunity_evidence

opportunity = {
    "type": "DOT_GAP",
    "ability_name": "Moonfire",
    "classification": "LIKELY_DOWNTIME",
    "confidence": "MEDIUM",
    "score": 50,
    "dot_evidence": {
        "_gap_start": 1000,
        "_gap_end": 5000,
        "target_count": 1,

        "temporal_coverage": {
            "123": {
                "coverage": "FULL",
                "gap_seconds": 4,
                "coverage_seconds": 4,
                "coverage_ratio": 1.0,
                "active_at_gap_start": True,
                "active_at_gap_end": True,
                "open_at_end": True,
                "intervals": [
                    [1000, 5000]
                ],
            }
        },

        "target_diagnostics": {
            "123": {
                "final_state": "ACTIVE",
                "explained_by": "ONGOING_AURA",
                "applied_during_gap": False,
                "refreshed_during_gap": False,
                "removed_during_gap": False,
                "stack_removals_during_gap": 0,
            }
        },
    },
}

evidence = build_opportunity_evidence(opportunity)

print("REALISTIC EVIDENCE TEST: PASS")
print("Strength:", evidence["evidence_strength"])
print("Coverage:", evidence["coverage"])
print("Final states:", evidence["final_states"])
print("Targets:", evidence["targets"])
print("Reason:", evidence["reason"])
