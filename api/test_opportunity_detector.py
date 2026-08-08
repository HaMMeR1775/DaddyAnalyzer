from opportunity_detector import (
    detect_opportunities,
    format_opportunities,
)


print("=" * 60)
print("DADDY ANALYZER - OPPORTUNITY DETECTOR TEST")
print("=" * 60)


# Small artificial test dataset.
# This lets us test the detector without running Warcraft Logs.

casts = [
    {
        "timestamp": 1000,
        "ability_name": "Starfire",
    },
    {
        "timestamp": 9000,
        "ability_name": "Starsurge",
    },
    {
        "timestamp": 16000,
        "ability_name": "Starfall",
    },
]


effects = [
    {
        "timestamp": 4000,
        "ability_name": "Eclipse (Solar)",
    },
]


damage_events = [
    {
        "timestamp": 5000,
        "ability_name": "Starfire",
    },
]


opportunities = detect_opportunities(
    class_name="Druid",
    spec_name="Balance",
    casts=casts,
    effects=effects,
    damage_events=damage_events,
    fight_start=0,
    fight_end=20000,
)


format_opportunities(opportunities)


print()
print("=" * 60)
print("OPPORTUNITY DETECTOR TEST COMPLETE")
print("=" * 60)