from collections import defaultdict


IMPORTANT_ABILITIES = {
    "Moonfire",
    "Sunfire",
    "Starsurge",
    "Starfall",
    "Starfire",
    "Wrath",
    "Fury of Elune",
    "Lunar Eclipse",
    "Eclipse (Lunar)",
    "Eclipse (Solar)",
    "Incarnation: Chosen of Elune",
}


DOT_ABILITIES = {
    "Moonfire",
    "Sunfire",
}


COOLDOWN_ABILITIES = {
    "Fury of Elune",
    "Incarnation: Chosen of Elune",
}


def _timestamp(event):
    return event.get("timestamp", 0)


def _ability_name(event):
    return event.get("abilityName") or event.get("name") or "Unknown"


def _event_type(event):
    return event.get("type", "")


def _is_damage(event):
    return _event_type(event) == "damage"


def _is_cast(event):
    return _event_type(event) == "cast"


def _is_effect(event):
    return _event_type(event) in {
        "applybuff",
        "removebuff",
        "refreshbuff",
        "applybuffstack",
        "removebuffstack",
        "applydebuff",
        "removedebuff",
        "refreshdebuff",
    }


def _is_player_cast(event):
    return _is_cast(event)


def _is_player_effect(event):
    return _is_effect(event)


def _damage_abilities_in_window(events, start, end):
    abilities = defaultdict(int)

    for event in events:
        timestamp = _timestamp(event)

        if timestamp < start or timestamp > end:
            continue

        if not _is_damage(event):
            continue

        name = _ability_name(event)

        if name != "Unknown":
            abilities[name] += 1

    return dict(abilities)


def _effects_in_window(events, start, end):
    result = []

    for event in events:
        timestamp = _timestamp(event)

        if start <= timestamp <= end and _is_effect(event):
            result.append(event)

    return result


def _has_active_effect(events, effect_name, timestamp):
    active = False

    relevant = sorted(
        [
            event
            for event in events
            if _ability_name(event) == effect_name
            and _timestamp(event) <= timestamp
        ],
        key=_timestamp,
    )

    for event in relevant:
        event_type = _event_type(event)

        if event_type in {
            "applybuff",
            "applybuffstack",
            "refreshbuff",
            "applydebuff",
            "refreshdebuff",
        }:
            active = True

        elif event_type in {
            "removebuff",
            "removebuffstack",
            "removedebuff",
        }:
            active = False

    return active


def _count_effect_applications(events, effect_name):
    return sum(
        1
        for event in events
        if _ability_name(event) == effect_name
        and _event_type(event)
        in {
            "applybuff",
            "applydebuff",
            "applybuffstack",
        }
    )


def _count_effect_refreshes(events, effect_name):
    return sum(
        1
        for event in events
        if _ability_name(event) == effect_name
        and _event_type(event)
        in {
            "refreshbuff",
            "refreshdebuff",
        }
    )


def _find_casts(casts, ability_name):
    return [
        cast
        for cast in casts
        if _ability_name(cast) == ability_name
    ]


def _find_damage(events, ability_name):
    return [
        event
        for event in events
        if _is_damage(event)
        and _ability_name(event) == ability_name
    ]


def analyze_moonfire(casts, effects, damage, fight_start, fight_end):
    moonfire_casts = _find_casts(casts, "Moonfire")
    applications = _count_effect_applications(effects, "Moonfire")
    refreshes = _count_effect_refreshes(effects, "Moonfire")

    if not moonfire_casts:
        return None

    damage_events = _find_damage(damage, "Moonfire")

    return {
        "ability": "Moonfire",
        "casts": len(moonfire_casts),
        "applications": applications,
        "refreshes": refreshes,
        "damage_events": len(damage_events),
        "targets": len(
            {
                event.get("targetID")
                for event in damage_events
                if event.get("targetID") is not None
            }
        ),
    }


def analyze_sunfire(casts, effects, damage, fight_start, fight_end):
    sunfire_casts = _find_casts(casts, "Sunfire")
    applications = _count_effect_applications(effects, "Sunfire")
    refreshes = _count_effect_refreshes(effects, "Sunfire")

    if not sunfire_casts:
        return None

    damage_events = _find_damage(damage, "Sunfire")

    return {
        "ability": "Sunfire",
        "casts": len(sunfire_casts),
        "applications": applications,
        "refreshes": refreshes,
        "damage_events": len(damage_events),
        "targets": len(
            {
                event.get("targetID")
                for event in damage_events
                if event.get("targetID") is not None
            }
        ),
    }


def analyze_starsurge(casts, damage):
    starsurge_casts = _find_casts(casts, "Starsurge")

    damage_events = _find_damage(damage, "Starsurge")

    return {
        "ability": "Starsurge",
        "casts": len(starsurge_casts),
        "damage_events": len(damage_events),
    }


def analyze_starfall(casts, damage):
    starfall_casts = _find_casts(casts, "Starfall")

    damage_events = _find_damage(damage, "Starfall")

    return {
        "ability": "Starfall",
        "casts": len(starfall_casts),
        "damage_events": len(damage_events),
    }


def analyze_starfire(casts, damage):
    starfire_casts = _find_casts(casts, "Starfire")

    damage_events = _find_damage(damage, "Starfire")

    return {
        "ability": "Starfire",
        "casts": len(starfire_casts),
        "damage_events": len(damage_events),
    }


def analyze_eclipse(casts, effects):
    lunar_casts = _find_casts(casts, "Lunar Eclipse")
    lunar_effects = [
        event
        for event in effects
        if _ability_name(event) == "Eclipse (Lunar)"
    ]

    solar_effects = [
        event
        for event in effects
        if _ability_name(event) == "Eclipse (Solar)"
    ]

    return {
        "lunar_casts": len(lunar_casts),
        "lunar_effects": len(lunar_effects),
        "solar_effects": len(solar_effects),
    }


def detect_dot_refresh_opportunities(
    casts,
    effects,
    damage,
    fight_start,
    fight_end,
):
    opportunities = []

    for dot_name in DOT_ABILITIES:
        dot_effects = [
            event
            for event in effects
            if _ability_name(event) == dot_name
        ]

        if not dot_effects:
            continue

        applications = [
            event
            for event in dot_effects
            if _event_type(event)
            in {
                "applydebuff",
                "applybuff",
                "applybuffstack",
            }
        ]

        refreshes = [
            event
            for event in dot_effects
            if _event_type(event)
            in {
                "refreshdebuff",
                "refreshbuff",
            }
        ]

        if not applications:
            continue

        for application in applications:
            timestamp = _timestamp(application)

            nearby_refreshes = [
                refresh
                for refresh in refreshes
                if 0 <= _timestamp(refresh) - timestamp <= 15_000
            ]

            if not nearby_refreshes:
                continue

        if len(refreshes) == 0 and len(applications) > 3:
            opportunities.append(
                {
                    "type": "DOT_REFRESH",
                    "ability": dot_name,
                    "severity": "MEDIUM",
                    "confidence": "LOW",
                    "reason": (
                        f"{dot_name} has multiple applications "
                        "but no recorded refresh events."
                    ),
                }
            )

    return opportunities


def detect_cast_gaps(
    casts,
    damage,
    minimum_gap=5.0,
):
    opportunities = []

    damage_related_casts = []

    damage_ability_names = {
        "Moonfire",
        "Sunfire",
        "Starsurge",
        "Starfall",
        "Starfire",
        "Wrath",
        "Fury of Elune",
    }

    for cast in casts:
        name = _ability_name(cast)

        if name in damage_ability_names:
            damage_related_casts.append(cast)

    damage_related_casts.sort(key=_timestamp)

    for previous, current in zip(
        damage_related_casts,
        damage_related_casts[1:],
    ):
        previous_time = _timestamp(previous)
        current_time = _timestamp(current)

        gap = (current_time - previous_time) / 1000.0

        if gap < minimum_gap:
            continue

        damage_during_gap = [
            event
            for event in damage
            if previous_time <= _timestamp(event) <= current_time
        ]

        if not damage_during_gap:
            severity = "HIGH"
            confidence = "HIGH"
            classification = "TRUE_DOWNTIME"

        else:
            severity = "LOW"
            confidence = "LOW"
            classification = "ONGOING_DAMAGE"

        opportunities.append(
            {
                "type": "CASTING_GAP",
                "timestamp": previous_time,
                "gap": round(gap, 2),
                "previous": _ability_name(previous),
                "next": _ability_name(current),
                "severity": severity,
                "confidence": confidence,
                "classification": classification,
                "damage_events": len(damage_during_gap),
            }
        )

    return opportunities


def detect_ability_opportunities(
    casts,
    effects,
    damage,
    fight_start,
    fight_end,
):
    opportunities = []

    moonfire = analyze_moonfire(
        casts,
        effects,
        damage,
        fight_start,
        fight_end,
    )

    sunfire = analyze_sunfire(
        casts,
        effects,
        damage,
        fight_start,
        fight_end,
    )

    starsurge = analyze_starsurge(
        casts,
        damage,
    )

    starfall = analyze_starfall(
        casts,
        damage,
    )

    starfire = analyze_starfire(
        casts,
        damage,
    )

    eclipse = analyze_eclipse(
        casts,
        effects,
    )

    dot_opportunities = detect_dot_refresh_opportunities(
        casts,
        effects,
        damage,
        fight_start,
        fight_end,
    )

    gap_opportunities = detect_cast_gaps(
        casts,
        damage,
        minimum_gap=5.0,
    )

    opportunities.extend(dot_opportunities)
    opportunities.extend(gap_opportunities)

    return {
        "moonfire": moonfire,
        "sunfire": sunfire,
        "starsurge": starsurge,
        "starfall": starfall,
        "starfire": starfire,
        "eclipse": eclipse,
        "opportunities": opportunities,
    }


def print_ability_analysis(result):
    print()
    print("ABILITY-SPECIFIC OPPORTUNITY ANALYSIS")
    print()
    print("=" * 50)

    for key in (
        "moonfire",
        "sunfire",
        "starsurge",
        "starfall",
        "starfire",
    ):
        data = result.get(key)

        if not data:
            continue

        print()
        print(data["ability"].upper())

        for field, value in data.items():
            if field == "ability":
                continue

            label = field.replace("_", " ").title()
            print(f"  {label}: {value}")

    print()
    print("=" * 50)
    print()

    opportunities = result.get("opportunities", [])

    print("IMPROVEMENT OPPORTUNITIES")
    print()
    print(f"Potential opportunities: {len(opportunities)}")

    if not opportunities:
        print("No ability-specific opportunities detected.")
        return

    for index, opportunity in enumerate(
        opportunities,
        start=1,
    ):
        print()
        print(
            f"{index}. "
            f"[{opportunity['severity']}] "
            f"{opportunity['type']}"
        )

        if "timestamp" in opportunity:
            print(
                f"   Time: "
                f"{opportunity['timestamp']}"
            )

        if "ability" in opportunity:
            print(
                f"   Ability: "
                f"{opportunity['ability']}"
            )

        if "previous" in opportunity:
            print(
                f"   Previous: "
                f"{opportunity['previous']}"
            )

        if "next" in opportunity:
            print(
                f"   Next: "
                f"{opportunity['next']}"
            )

        if "gap" in opportunity:
            print(
                f"   Gap: "
                f"{opportunity['gap']:.1f}s"
            )

        print(
            f"   Confidence: "
            f"{opportunity['confidence']}"
        )

        if "classification" in opportunity:
            print(
                f"   Classification: "
                f"{opportunity['classification']}"
            )

        if "damage_events" in opportunity:
            print(
                f"   Damage during gap: "
                f"{opportunity['damage_events']}"
            )