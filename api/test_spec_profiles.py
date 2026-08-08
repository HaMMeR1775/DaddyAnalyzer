from spec_profiles import (
    get_spec_profile,
    get_ability_profile,
    get_abilities_by_category,
)


print("=" * 60)
print("DADDY ANALYZER - SPEC PROFILE TEST")
print("=" * 60)


profile = get_spec_profile(
    "Druid",
    "Balance",
)


print()
print("SPEC")
print(f"Class: {profile['class']}")
print(f"Spec:  {profile['spec']}")


print()
print("ABILITY COUNT")
print(len(profile["abilities"]))


print()
print("DOT ABILITIES")

for ability in profile["dot_abilities"]:
    print(f"- {ability}")


print()
print("BUILDER ABILITIES")

for ability in profile["builder_abilities"]:
    print(f"- {ability}")


print()
print("SPENDER ABILITIES")

for ability in profile["spender_abilities"]:
    print(f"- {ability}")


print()
print("COOLDOWNS")

for ability in profile["cooldown_abilities"]:
    print(f"- {ability}")


print()
print("DEFENSIVES")

for ability in profile["defensive_abilities"]:
    print(f"- {ability}")


print()
print("UTILITY")

for ability in profile["utility_abilities"]:
    print(f"- {ability}")


print()
print("MOVEMENT")

for ability in profile["movement_abilities"]:
    print(f"- {ability}")


print()
print("IMPORTANT EFFECTS")

for effect in profile["important_effects"]:
    print(f"- {effect}")


print()
print("STARFIRE PROFILE")

starfire = get_ability_profile(
    "Druid",
    "Balance",
    "Starfire",
)

print(starfire)


print()
print("CATEGORY TESTS")

categories = [
    "dot",
    "builder",
    "spender",
    "cooldown",
    "defensive",
    "utility",
    "movement",
    "form",
    "buff",
]

for category in categories:
    abilities = get_abilities_by_category(
        "Druid",
        "Balance",
        category,
    )

    print()
    print(f"{category.upper()}")

    if not abilities:
        print("- None")
    else:
        for name in abilities:
            print(f"- {name}")


print()
print("KNOWN ABILITY TESTS")

test_abilities = [
    "Moonfire",
    "Sunfire",
    "Starfire",
    "Wrath",
    "Starsurge",
    "Starfall",
    "Incarnation: Chosen of Elune",
    "Fury of Elune",
    "Solar Beam",
    "Barkskin",
    "Remove Corruption",
    "Definitely Not A Real Ability",
]

for ability in test_abilities:
    result = get_ability_profile(
        "Druid",
        "Balance",
        ability,
    )

    print(
        f"{ability}: "
        f"{'KNOWN' if result else 'UNKNOWN'}"
    )


print()
print("=" * 60)
print("SPEC PROFILE TEST COMPLETE")
print("=" * 60)