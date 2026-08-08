from opportunity_evidence import build_opportunity_evidence

opportunity = {
    "type": "DOT_GAP",
    "ability_name": "Moonfire",
    "classification": "LIKELY_DOWNTIME",
    "confidence": "MEDIUM",
    "score": 50,
    "dot_evidence": {
        "target_count": 1,
        "active_targets_before_gap": [123],
        "targets_during_gap": [],
        "applications_during_gap": 0,
        "refreshes_during_gap": 0,
        "removals_during_gap": 0,
        "stack_removals_during_gap": 0,
    },
}

evidence = build_opportunity_evidence(opportunity)

print("Evidence smoke test: PASS")
print("Version:", evidence["evidence_version"])
print("Type:", evidence["type"])
print("Ability:", evidence["ability"])
print("Strength:", evidence["evidence_strength"])
print("Coverage:", evidence["coverage"])
print("Final states:", evidence["final_states"])
