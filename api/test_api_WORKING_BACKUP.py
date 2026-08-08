from urllib.parse import urlparse

from warcraft_logs import WarcraftLogsAPI

from opportunity_detector import (
    detect_opportunities,
    format_opportunities,
)


TEST_REPORT_URL = (
    "https://www.warcraftlogs.com/reports/"
    "71kCmQ9jaRdcr4LZ?type=summary&fight=3"
)

FIGHT_ID = 3
PLAYER_ID = 3

MIN_CAST_GAP_MS = 5000
CONTEXT_WINDOW_MS = 3000


def extract_report_code(value):
    value = value.strip()

    if "/reports/" in value:
        parsed = urlparse(value)
        parts = parsed.path.strip("/").split("/")

        if len(parts) >= 2 and parts[0] == "reports":
            return parts[1]

    return value


def get_fight(api, report_code, fight_id):
    query = """
    query GetFight(
        $code: String,
        $fightIDs: [Int]
    ) {
        reportData {
            report(code: $code) {
                fights(
                    fightIDs: $fightIDs
                ) {
                    id
                    name
                    startTime
                    endTime
                    kill
                    difficulty
                }
            }
        }
    }
    """

    result = api.query(
        query,
        {
            "code": report_code,
            "fightIDs": [fight_id],
        }
    )

    report = result["reportData"]["report"]

    if report is None:
        raise RuntimeError("Report not found.")

    fights = report["fights"]

    if not fights:
        raise RuntimeError(
            f"Fight {fight_id} not found."
        )

    return fights[0]


def get_ability_names(api, report_code):
    query = """
    query GetMasterData($code: String) {
        reportData {
            report(code: $code) {
                masterData {
                    abilities {
                        gameID
                        name
                    }
                }
            }
        }
    }
    """

    result = api.query(
        query,
        {
            "code": report_code
        }
    )

    report = result["reportData"]["report"]

    return {
        ability["gameID"]: ability["name"]
        for ability in report["masterData"]["abilities"]
    }


def build_cast_timeline(
    events,
    player_id,
    ability_names,
    fight_start
):
    casts = []

    for event in events:

        if event.get("type") != "cast":
            continue

        if event.get("sourceID") != player_id:
            continue

        timestamp = event.get("timestamp")
        ability_id = event.get("abilityGameID")

        casts.append({
            "timestamp": timestamp,
            "relative_time": (
                timestamp - fight_start
            ),
            "ability_id": ability_id,
            "name": ability_names.get(
                ability_id,
                f"Unknown Ability ({ability_id})"
            ),
        })

    casts.sort(
        key=lambda cast: cast["timestamp"]
    )

    return casts


def build_effect_timeline(
    events,
    player_id,
    ability_names
):
    effect_types = {
        "applybuff",
        "applybuffstack",
        "refreshbuff",
        "removebuff",
        "removebuffstack",
        "applydebuff",
        "refreshdebuff",
        "removedebuff",
        "removedebuffstack",
    }

    effects = []

    for event in events:

        if event.get("type") not in effect_types:
            continue

        if event.get("targetID") != player_id:
            continue

        timestamp = event.get("timestamp")
        ability_id = event.get("abilityGameID")

        effects.append({
            "timestamp": timestamp,
            "type": event.get("type"),
            "ability_id": ability_id,
            "name": ability_names.get(
                ability_id,
                f"Unknown Ability ({ability_id})"
            ),
            "source_id": event.get("sourceID"),
            "target_id": event.get("targetID"),
            "stack": event.get("stack"),
        })

    effects.sort(
        key=lambda effect:
        effect["timestamp"]
    )

    return effects


def build_outgoing_effect_timeline(
    events,
    player_id,
    ability_names
):
    effect_types = {
        "applydebuff",
        "refreshdebuff",
        "removedebuff",
        "removedebuffstack",
        "applybuff",
        "refreshbuff",
        "removebuff",
        "removebuffstack",
    }

    effects = []

    for event in events:

        if event.get("type") not in effect_types:
            continue

        if event.get("sourceID") != player_id:
            continue

        timestamp = event.get("timestamp")
        ability_id = event.get("abilityGameID")

        effects.append({
            "timestamp": timestamp,
            "type": event.get("type"),
            "ability_id": ability_id,
            "name": ability_names.get(
                ability_id,
                f"Unknown Ability ({ability_id})"
            ),
            "source_id": event.get("sourceID"),
            "target_id": event.get("targetID"),
            "stack": event.get("stack"),
        })

    effects.sort(
        key=lambda effect:
        effect["timestamp"]
    )

    return effects


def build_damage_timeline(
    events,
    player_id,
    ability_names
):
    damage = []

    for event in events:

        if event.get("type") != "damage":
            continue

        if event.get("sourceID") != player_id:
            continue

        timestamp = event.get("timestamp")
        ability_id = event.get("abilityGameID")

        damage.append({
            "timestamp": timestamp,
            "ability_id": ability_id,
            "name": ability_names.get(
                ability_id,
                f"Unknown Ability ({ability_id})"
            ),
            "target_id": event.get("targetID"),
            "target_instance": event.get(
                "targetInstance"
            ),
            "amount": event.get("amount", 0),
            "unmitigated_amount": event.get(
                "unmitigatedAmount",
                0
            ),
            "is_aoe": event.get(
                "isAoE",
                False
            ),
            "is_tick": event.get(
                "tick",
                False
            ),
            "hit_type": event.get(
                "hitType"
            ),
        })

    damage.sort(
        key=lambda event:
        event["timestamp"]
    )

    return damage


def build_combined_timeline(
    casts,
    effects,
    damage
):
    timeline = []

    for cast in casts:
        timeline.append({
            "timestamp": cast["timestamp"],
            "type": "CAST",
            "name": cast["name"],
            "ability_id": cast["ability_id"],
            "data": cast,
        })

    for effect in effects:
        timeline.append({
            "timestamp": effect["timestamp"],
            "type": "EFFECT",
            "name": effect["name"],
            "ability_id": effect["ability_id"],
            "data": effect,
        })

    for hit in damage:
        timeline.append({
            "timestamp": hit["timestamp"],
            "type": "DAMAGE",
            "name": hit["name"],
            "ability_id": hit["ability_id"],
            "data": hit,
        })

    timeline.sort(
        key=lambda event:
        event["timestamp"]
    )

    return timeline


def find_cast_gaps(
    casts,
    fight_start,
    fight_end
):
    gaps = []

    if not casts:
        return gaps

    first_gap = (
        casts[0]["timestamp"]
        - fight_start
    )

    for index in range(1, len(casts)):

        previous = casts[index - 1]
        current = casts[index]

        gap = (
            current["timestamp"]
            - previous["timestamp"]
        )

        if gap >= MIN_CAST_GAP_MS:

            gaps.append({
                "type": "CAST_GAP",
                "timestamp": previous["timestamp"],
                "start": previous["timestamp"],
                "end": current["timestamp"],
                "gap_ms": gap,
                "previous": previous["name"],
                "next": current["name"],
            })

    return gaps


def get_events_between(
    events,
    start_time,
    end_time
):
    return [
        event
        for event in events
        if (
            start_time
            <= event["timestamp"]
            <= end_time
        )
    ]


def analyze_gap_context(
    gap,
    casts,
    effects,
    outgoing_effects,
    damage
):
    start = gap["start"]
    end = gap["end"]

    nearby_damage = get_events_between(
        damage,
        start,
        end
    )

    nearby_effects = get_events_between(
        effects,
        start,
        end
    )

    nearby_outgoing_effects = (
        get_events_between(
            outgoing_effects,
            start,
            end
        )
    )

    utility_names = {
        "Travel Form",
        "Cat Form",
        "Bear Form",
        "Dash",
        "Stampeding Roar",
        "Wild Charge",
        "Solar Beam",
        "Barkskin",
        "Remove Corruption",
    }

    utility_events = [
        event
        for event in casts
        if (
            start <= event["timestamp"] <= end
            and event["name"] in utility_names
        )
    ]

    damage_names = sorted({
        event["name"]
        for event in nearby_damage
    })

    effect_names = sorted({
        event["name"]
        for event in nearby_effects
    })

    outgoing_names = sorted({
        event["name"]
        for event in nearby_outgoing_effects
    })

    gap_seconds = (
        gap["gap_ms"] / 1000
    )

    if utility_events:

        classification = "UTILITY / MOVEMENT"
        confidence = "LOW"

        explanation = (
            "Utility or movement activity occurred "
            "during the gap."
        )

    elif nearby_damage:

        classification = "ONGOING DAMAGE"
        confidence = "LOW"

        explanation = (
            "Damage continued during the gap, so "
            "this is not confirmed downtime."
        )

    elif nearby_effects or nearby_outgoing_effects:

        classification = "COMBAT ACTIVITY"
        confidence = "LOW"

        explanation = (
            "Combat effects occurred during the gap. "
            "Additional ability-specific analysis is "
            "required."
        )

    elif gap_seconds >= 10:

        classification = "LIKELY DOWNTIME"
        confidence = "MEDIUM"

        explanation = (
            "No player damage, utility or relevant "
            "effect activity was detected."
        )

    else:

        classification = "POTENTIAL DOWNTIME"
        confidence = "LOW"

        explanation = (
            "The player had no recorded damage cast "
            "during this period."
        )

    return {
        "classification": classification,
        "confidence": confidence,
        "explanation": explanation,
        "damage_events": len(nearby_damage),
        "effect_events": len(nearby_effects),
        "outgoing_effect_events": len(
            nearby_outgoing_effects
        ),
        "damage_abilities": damage_names,
        "effects": effect_names,
        "outgoing_effects": outgoing_names,
    }


def detect_contextual_gaps(
    casts,
    effects,
    outgoing_effects,
    damage
):
    opportunities = []

    damage_abilities = {
        "Starfire",
        "Starfall",
        "Starsurge",
        "Moonfire",
        "Sunfire",
        "Wrath",
        "Fury of Elune",
        "Lunar Eclipse",
        "Incarnation: Chosen of Elune",
    }

    ignored_abilities = {
        "Moonkin Form",
        "Travel Form",
        "Cat Form",
        "Bear Form",
        "Dash",
        "Stampeding Roar",
        "Wild Charge",
        "Solar Beam",
        "Barkskin",
        "Remove Corruption",
        "Light's Potential",
        "Emberwing Heatwave",
    }

    gaps = find_cast_gaps(
        casts,
        casts[0]["timestamp"],
        casts[-1]["timestamp"]
    )

    for gap in gaps:

        if gap["previous"] in ignored_abilities:
            continue

        if gap["next"] in ignored_abilities:
            continue

        if gap["previous"] not in damage_abilities:
            continue

        if gap["next"] not in damage_abilities:
            continue

        context = analyze_gap_context(
            gap,
            casts,
            effects,
            outgoing_effects,
            damage
        )

        gap_seconds = (
            gap["gap_ms"] / 1000
        )

        severity = "MEDIUM"

        if (
            gap_seconds >= 8
            and context["classification"]
            == "LIKELY DOWNTIME"
        ):
            severity = "HIGH"

        if (
            context["classification"]
            == "UTILITY / MOVEMENT"
        ):
            severity = "INFO"

        opportunities.append({
            "category": "CASTING_GAP",
            "severity": severity,
            "timestamp": gap["timestamp"],
            "duration": gap_seconds,
            "previous": gap["previous"],
            "next": gap["next"],
            "context": context,
        })

    return opportunities


def detect_dot_activity(
    outgoing_effects
):
    dot_names = {
        "Moonfire",
        "Sunfire",
    }

    dot_events = [
        event
        for event in outgoing_effects
        if (
            event["name"] in dot_names
            and event["type"] in {
                "applydebuff",
                "refreshdebuff",
            }
        )
    ]

    by_dot = {}

    for event in dot_events:

        name = event["name"]

        if name not in by_dot:
            by_dot[name] = []

        by_dot[name].append(event)

    return by_dot


def analyze_dot_activity(
    outgoing_effects
):
    dot_activity = detect_dot_activity(
        outgoing_effects
    )

    results = []

    for dot_name, events in dot_activity.items():

        targets = {}

        for event in events:

            target_id = event["target_id"]

            if target_id not in targets:
                targets[target_id] = []

            targets[target_id].append(
                event["timestamp"]
            )

        total_applications = len(events)

        unique_targets = len(targets)

        refreshes = sum(
            1
            for event in events
            if event["type"]
            == "refreshdebuff"
        )

        applications = sum(
            1
            for event in events
            if event["type"]
            == "applydebuff"
        )

        results.append({
            "name": dot_name,
            "applications": applications,
            "refreshes": refreshes,
            "unique_targets": unique_targets,
            "events": len(events),
        })

    return results


def print_contextual_opportunities(
    opportunities,
    fight_start
):
    print()
    print("CONTEXTUAL IMPROVEMENT ANALYSIS")
    print()

    if not opportunities:
        print(
            "No contextual opportunities detected."
        )
        return

    print(
        f"Potential opportunities: "
        f"{len(opportunities)}"
    )

    print()

    for index, opportunity in enumerate(
        opportunities[:20],
        start=1
    ):

        relative = (
            opportunity["timestamp"]
            - fight_start
        ) / 1000

        context = opportunity["context"]

        print(
            f"{index}. "
            f"[{opportunity['severity']}] "
            f"{relative:.2f}s | "
            f"{opportunity['duration']:.1f}s | "
            f"{opportunity['previous']} -> "
            f"{opportunity['next']}"
        )

        print(
            f"   Classification: "
            f"{context['classification']}"
        )

        print(
            f"   Confidence: "
            f"{context['confidence']}"
        )

        print(
            f"   Evidence: "
            f"{context['explanation']}"
        )

        print(
            f"   Damage events: "
            f"{context['damage_events']}"
        )

        print(
            f"   Effect events: "
            f"{context['effect_events']}"
        )

        print(
            f"   Outgoing effects: "
            f"{context['outgoing_effect_events']}"
        )

        if context["damage_abilities"]:

            print(
                "   Damage abilities: "
                + ", ".join(
                    context["damage_abilities"]
                )
            )

        if context["outgoing_effects"]:

            print(
                "   Outgoing effects: "
                + ", ".join(
                    context["outgoing_effects"]
                )
            )

        print()

    if len(opportunities) > 20:

        print(
            f"... {len(opportunities) - 20} "
            "additional opportunities stored "
            "internally"
        )


def print_dot_analysis(
    dot_results
):
    print()
    print("DOT ACTIVITY ANALYSIS")
    print()

    if not dot_results:

        print(
            "No Moonfire or Sunfire activity detected."
        )

        return

    for result in dot_results:

        print(
            f"{result['name']}: "
            f"{result['applications']} applications | "
            f"{result['refreshes']} refreshes | "
            f"{result['unique_targets']} targets"
        )


def print_data_summary(
    casts,
    effects,
    outgoing_effects,
    damage
):
    print()
    print("COMBAT DATA SUMMARY")
    print()

    print(
        f"Casts:              {len(casts)}"
    )

    print(
        f"Player effects:     {len(effects)}"
    )

    print(
        f"Outgoing effects:   {len(outgoing_effects)}"
    )

    print(
        f"Damage events:      {len(damage)}"
    )


def main():

    print("Connecting to Warcraft Logs...")

    api = WarcraftLogsAPI()

    try:

        api.authenticate()

        print(
            "SUCCESS: Authentication works!"
        )

        report_code = extract_report_code(
            TEST_REPORT_URL
        )

        print(
            f"Using test report: "
            f"{report_code}"
        )

        print()
        print("Fetching fight information...")

        fight = get_fight(
            api,
            report_code,
            FIGHT_ID
        )

        fight_start = fight["startTime"]
        fight_end = fight["endTime"]

        print()
        print("FIGHT CONTEXT")
        print()

        print(
            f"Fight:       {fight['name']}"
        )

        print(
            f"Difficulty:  {fight['difficulty']}"
        )

        print(
            f"Kill:        {fight['kill']}"
        )

        print(
            f"Duration:    "
            f"{(fight_end - fight_start) / 1000:.2f}s"
        )

        print()
        print("Fetching ALL player events...")

        events = api.get_all_player_events(
            report_code,
            FIGHT_ID,
            PLAYER_ID
        )

        print()
        print(
            f"Total events received: "
            f"{len(events)}"
        )

        print()
        print("Fetching ability names...")

        ability_names = get_ability_names(
            api,
            report_code
        )

        print()
        print("Building combat data...")

        casts = build_cast_timeline(
            events,
            PLAYER_ID,
            ability_names,
            fight_start
        )

        effects = build_effect_timeline(
            events,
            PLAYER_ID,
            ability_names
        )

        outgoing_effects = (
            build_outgoing_effect_timeline(
                events,
                PLAYER_ID,
                ability_names
            )
        )

        damage = build_damage_timeline(
            events,
            PLAYER_ID,
            ability_names
        )

        timeline = build_combined_timeline(
            casts,
            effects,
            damage
        )

        print_data_summary(
            casts,
            effects,
            outgoing_effects,
            damage
        )

        print(
            f"Combined timeline: "
            f"{len(timeline)}"
        )

        print()
        print(
            "Running contextual opportunity "
            "detection..."
        )

        # The new detector uses generic field names.
        # Convert the existing combat data without
        # changing the original timelines.

        detector_casts = [
            {
                "timestamp": cast["timestamp"],
                "ability_name": cast["name"],
            }
            for cast in casts
        ]

        detector_effects = [
            {
                "timestamp": effect["timestamp"],
                "ability_name": effect["name"],
            }
            for effect in effects
        ]

        detector_damage = [
            {
                "timestamp": event["timestamp"],
                "ability_name": event["name"],
            }
            for event in damage
        ]

        opportunities = detect_opportunities(
            class_name="Druid",
            spec_name="Balance",
            casts=detector_casts,
            effects=detector_effects,
            damage_events=detector_damage,
            fight_start=fight_start,
            fight_end=fight_end,
        )

        format_opportunities(
            opportunities
        )

        print()
        print(
            "Analyzing DoT activity..."
        )

        dot_results = analyze_dot_activity(
            outgoing_effects
        )

        print_dot_analysis(
            dot_results
        )

        print()
        print("ANALYSIS COMPLETE")

        print()
        print(
            "The system now distinguishes "
            "potential downtime from combat activity."
        )

        print(
            "No issue is treated as a confirmed "
            "mistake without supporting evidence."
        )

        print()
        print(
            "NEXT STEP: ABILITY-SPECIFIC "
            "OPPORTUNITY DETECTION"
        )

    except Exception as error:

        print()
        print("ERROR:")
        print(error)


if __name__ == "__main__":
    main()

===== OPPORTUNITY DETECTOR =====
"""
Opportunity detection for DaddyAnalyzer.

The detector is intentionally spec-agnostic.
Spec-specific abilities and metadata are supplied by spec_profiles.py.

The detector does not declare gameplay mistakes as facts.
It produces evidence-based opportunities that can be evaluated later.
"""

from spec_profiles import get_spec_profile


# ============================================================
# PUBLIC API
# ============================================================

def detect_opportunities(
    class_name,
    spec_name,
    casts,
    effects,
    damage_events,
    fight_start,
    fight_end,
):
    """
    Analyze combat data and return potential improvement opportunities.

    The detector is spec-agnostic. All ability classification comes
    from the selected spec profile.

    Current analysis:

    1. Contextual cast gaps
    2. Damage activity during those gaps
    3. Ability-category context
    4. DoT activity context
    5. Conservative evidence/confidence scoring

    No opportunity is automatically considered a confirmed mistake.
    """

    profile = get_spec_profile(
        class_name,
        spec_name,
    )

    if not casts:
        return []

    opportunities = []

    # --------------------------------------------------------
    # Build profile-driven ability groups
    # --------------------------------------------------------

    ability_profiles = profile.get(
        "abilities",
        {},
    )

    damage_abilities = {
        ability_name
        for ability_name, ability_data in ability_profiles.items()
        if ability_data.get("role") == "damage"
    }

    dot_abilities = set(
        profile.get(
            "dot_abilities",
            [],
        )
    )

    builder_abilities = set(
        profile.get(
            "builder_abilities",
            [],
        )
    )

    spender_abilities = set(
        profile.get(
            "spender_abilities",
            [],
        )
    )

    cooldown_abilities = set(
        profile.get(
            "cooldown_abilities",
            [],
        )
    )

    # --------------------------------------------------------
    # Normalize and sort casts
    # --------------------------------------------------------

    normalized_casts = [
        cast
        for cast in casts
        if cast.get("timestamp") is not None
    ]

    normalized_casts.sort(
        key=lambda event: event["timestamp"]
    )

    # --------------------------------------------------------
    # Damage-related casts
    # --------------------------------------------------------

    relevant_casts = [
        cast
        for cast in normalized_casts
        if cast.get("ability_name") in damage_abilities
    ]

    # --------------------------------------------------------
    # Contextual cast-gap detection
    # --------------------------------------------------------

    contextual_opportunities = _detect_casting_gaps(
        relevant_casts=relevant_casts,
        effects=effects,
        damage_events=damage_events,
        dot_abilities=dot_abilities,
        builder_abilities=builder_abilities,
        spender_abilities=spender_abilities,
        cooldown_abilities=cooldown_abilities,
    )

    opportunities.extend(
        contextual_opportunities
    )

    # --------------------------------------------------------
    # Ability-specific analysis
    # --------------------------------------------------------

    ability_opportunities = _detect_ability_specific_opportunities(
        casts=normalized_casts,
        effects=effects,
        damage_events=damage_events,
        profile=profile,
    )

    opportunities.extend(
        ability_opportunities
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    opportunities = _deduplicate_opportunities(
        opportunities
    )

    # --------------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------------

    opportunities.sort(
        key=lambda opportunity: (
            opportunity.get("timestamp", 0),
            opportunity.get("type", ""),
        )
    )

    return opportunities


# ============================================================
# CONTEXTUAL CAST GAP ANALYSIS
# ============================================================

def _detect_casting_gaps(
    relevant_casts,
    effects,
    damage_events,
    dot_abilities,
    builder_abilities,
    spender_abilities,
    cooldown_abilities,
):
    """
    Detect gaps between damage-related casts.

    A gap is only a potential opportunity.

    Existing damage/effect activity lowers confidence that the player
    was actually inactive.
    """

    opportunities = []

    if len(relevant_casts) < 2:
        return opportunities

    for index in range(
        len(relevant_casts) - 1
    ):
        previous_cast = relevant_casts[index]
        next_cast = relevant_casts[index + 1]

        previous_time = previous_cast["timestamp"]
        next_time = next_cast["timestamp"]

        gap_ms = next_time - previous_time
        gap_seconds = gap_ms / 1000.0

        # Five seconds is intentionally conservative.
        if gap_seconds < 5.0:
            continue

        damage_during_gap = _events_between(
            damage_events,
            previous_time,
            next_time,
        )

        effects_during_gap = _events_between(
            effects,
            previous_time,
            next_time,
        )

        previous_ability = previous_cast.get(
            "ability_name",
            "Unknown",
        )

        next_ability = next_cast.get(
            "ability_name",
            "Unknown",
        )

        classification = _classify_gap(
            damage_during_gap=damage_during_gap,
            effects_during_gap=effects_during_gap,
        )

        confidence = _calculate_confidence(
            gap_seconds=gap_seconds,
            classification=classification,
            damage_events=len(
                damage_during_gap
            ),
            effect_events=len(
                effects_during_gap
            ),
        )

        severity = _calculate_severity(
            gap_seconds=gap_seconds,
            classification=classification,
            confidence=confidence,
        )

        evidence = _build_gap_evidence(
            classification=classification,
            damage_count=len(
                damage_during_gap
            ),
            effect_count=len(
                effects_during_gap
            ),
        )

        opportunities.append(
            {
                "type": "CASTING_GAP",
                "timestamp": previous_time,
                "gap_seconds": gap_seconds,
                "previous_ability": previous_ability,
                "next_ability": next_ability,
                "severity": severity,
                "classification": classification,
                "confidence": confidence,
                "evidence": evidence,
                "damage_events": len(
                    damage_during_gap
                ),
                "effect_events": len(
                    effects_during_gap
                ),
                "context": _build_ability_context(
                    previous_ability=previous_ability,
                    next_ability=next_ability,
                    dot_abilities=dot_abilities,
                    builder_abilities=builder_abilities,
                    spender_abilities=spender_abilities,
                    cooldown_abilities=cooldown_abilities,
                ),
            }
        )

    return opportunities


# ============================================================
# ABILITY-SPECIFIC ANALYSIS
# ============================================================

def _detect_ability_specific_opportunities(
    casts,
    effects,
    damage_events,
    profile,
):
    """
    Run profile-driven ability-specific analysis.

    This function intentionally starts conservatively.

    The profile tells us WHAT an ability is.
    Combat data tells us WHAT actually happened.

    We do not invent cooldown durations, resource values, target
    requirements, or encounter mechanics that are not present in
    the supplied data.
    """

    opportunities = []

    abilities = profile.get(
        "abilities",
        {}
    )

    dot_abilities = set(
        profile.get(
            "dot_abilities",
            []
        )
    )

    spender_abilities = set(
        profile.get(
            "spender_abilities",
            []
        )
    )

    cooldown_abilities = set(
        profile.get(
            "cooldown_abilities",
            []
        )
    )

    # --------------------------------------------------------
    # DOT ANALYSIS
    # --------------------------------------------------------

    for ability_name in dot_abilities:
        ability_data = abilities.get(
            ability_name,
            {},
        )

        if not ability_data.get(
            "track_uptime",
            False,
        ):
            continue

        ability_casts = [
            cast
            for cast in casts
            if cast.get("ability_name")
            == ability_name
        ]

        if not ability_casts:
            continue

        ability_casts.sort(
            key=lambda event: event["timestamp"]
        )

        for index in range(
            len(ability_casts) - 1
        ):
            current_cast = ability_casts[index]
            next_cast = ability_casts[index + 1]

            current_time = current_cast[
                "timestamp"
            ]

            next_time = next_cast[
                "timestamp"
            ]

            gap_seconds = (
                next_time - current_time
            ) / 1000.0

            # Do not assume a specific DoT duration here.
            # We only report unusually large gaps as candidates.
            if gap_seconds < 12.0:
                continue

            damage_during_gap = _events_between(
                damage_events,
                current_time,
                next_time,
            )

            effects_during_gap = _events_between(
                effects,
                current_time,
                next_time,
            )

            opportunities.append(
                {
                    "type": "DOT_GAP",
                    "timestamp": current_time,
                    "gap_seconds": gap_seconds,
                    "ability": ability_name,
                    "severity": (
                        "MEDIUM"
                        if gap_seconds >= 20.0
                        else "LOW"
                    ),
                    "classification": (
                        "POTENTIAL_DOT_UPTIME_LOSS"
                    ),
                    "confidence": "LOW",
                    "evidence": (
                        "A long interval occurred between "
                        f"{ability_name} casts. "
                        "The available combat data does not "
                        "yet prove that the effect was absent "
                        "from every relevant target."
                    ),
                    "damage_events": len(
                        damage_during_gap
                    ),
                    "effect_events": len(
                        effects_during_gap
                    ),
                }
            )

    # --------------------------------------------------------
    # SPENDER ANALYSIS
    # --------------------------------------------------------

    for ability_name in spender_abilities:
        ability_data = abilities.get(
            ability_name,
            {},
        )

        if not ability_data.get(
            "track_usage",
            False,
        ):
            continue

        ability_casts = [
            cast
            for cast in casts
            if cast.get("ability_name")
            == ability_name
        ]

        if not ability_casts:
            continue

        # We deliberately do NOT call missing spender casts
        # mistakes because resource state is not available here.
        #
        # Instead, this establishes the data point so a later
        # resource-aware detector can use it.

        if len(ability_casts) == 1:
            continue

    # --------------------------------------------------------
    # COOLDOWN ANALYSIS
    # --------------------------------------------------------

    for ability_name in cooldown_abilities:
        ability_data = abilities.get(
            ability_name,
            {},
        )

        if not ability_data.get(
            "track_usage",
            False,
        ):
            continue

        ability_casts = [
            cast
            for cast in casts
            if cast.get("ability_name")
            == ability_name
        ]

        if not ability_casts:
            continue

        # We intentionally do not report cooldown misuse yet.
        #
        # A cooldown cannot be judged correctly without:
        #
        # - cooldown duration
        # - encounter duration
        # - available charges
        # - fight mechanics
        # - target availability
        # - resource state
        #
        # Those rules will be added later.

    return opportunities


# ============================================================
# CLASSIFICATION
# ============================================================

def _classify_gap(
    damage_during_gap,
    effects_during_gap,
):
    """
    Classify a gap using observable combat activity.
    """

    if damage_during_gap:
        return "ONGOING DAMAGE"

    if effects_during_gap:
        return "COMBAT ACTIVITY"

    return "POTENTIAL DOWNTIME"


def _calculate_confidence(
    gap_seconds,
    classification,
    damage_events,
    effect_events,
):
    """
    Conservative confidence calculation.
    """

    if classification == "POTENTIAL DOWNTIME":
        if gap_seconds >= 10.0:
            return "MEDIUM"

        return "LOW"

    if classification == "COMBAT ACTIVITY":
        return "LOW"

    if damage_events >= 10:
        return "LOW"

    return "LOW"


def _calculate_severity(
    gap_seconds,
    classification,
    confidence,
):
    """
    Assign conservative severity.

    Severity is not the same as certainty.
    """

    if classification == "ONGOING DAMAGE":
        if gap_seconds >= 15.0:
            return "MEDIUM"

        return "LOW"

    if classification == "COMBAT ACTIVITY":
        return "LOW"

    if confidence == "MEDIUM":
        if gap_seconds >= 10.0:
            return "HIGH"

        return "MEDIUM"

    if gap_seconds >= 10.0:
        return "MEDIUM"

    return "LOW"


# ============================================================
# EVIDENCE
# ============================================================

def _build_gap_evidence(
    classification,
    damage_count,
    effect_count,
):
    """
    Build human-readable evidence.
    """

    if classification == "ONGOING DAMAGE":
        return (
            "Damage continued during the gap, "
            "so this is not confirmed downtime."
        )

    if classification == "COMBAT ACTIVITY":
        return (
            "Combat-related effects continued during "
            "the gap, so the player was not necessarily idle."
        )

    return (
        "No damage or effect events were detected "
        "during the gap between damage-related casts."
    )


# ============================================================
# ABILITY CONTEXT
# ============================================================

def _build_ability_context(
    previous_ability,
    next_ability,
    dot_abilities,
    builder_abilities,
    spender_abilities,
    cooldown_abilities,
):
    """
    Describe the profile categories involved in a cast transition.
    """

    return {
        "previous": _get_ability_category(
            previous_ability,
            dot_abilities,
            builder_abilities,
            spender_abilities,
            cooldown_abilities,
        ),
        "next": _get_ability_category(
            next_ability,
            dot_abilities,
            builder_abilities,
            spender_abilities,
            cooldown_abilities,
        ),
    }


def _get_ability_category(
    ability_name,
    dot_abilities,
    builder_abilities,
    spender_abilities,
    cooldown_abilities,
):
    if ability_name in dot_abilities:
        return "dot"

    if ability_name in builder_abilities:
        return "builder"

    if ability_name in spender_abilities:
        return "spender"

    if ability_name in cooldown_abilities:
        return "cooldown"

    return "other"


# ============================================================
# EVENT HELPERS
# ============================================================

def _events_between(
    events,
    start_time,
    end_time,
):
    """
    Return events occurring between two timestamps.
    """

    if not events:
        return []

    return [
        event
        for event in events
        if (
            event.get("timestamp") is not None
            and start_time
            <= event["timestamp"]
            <= end_time
        )
    ]


# ============================================================
# DEDUPLICATION
# ============================================================

def _deduplicate_opportunities(
    opportunities,
):
    """
    Remove duplicate opportunities.

    Contextual CASTING_GAP and DOT_GAP can describe the same
    moment, but they represent different analyses. They are
    therefore only considered duplicates when their type,
    timestamp and ability identity all match.
    """

    unique = {}
    result = []

    for opportunity in opportunities:
        opportunity_type = opportunity.get(
            "type",
            "UNKNOWN",
        )

        timestamp = opportunity.get(
            "timestamp",
            0,
        )

        previous_ability = opportunity.get(
            "previous_ability",
            "",
        )

        next_ability = opportunity.get(
            "next_ability",
            "",
        )

        ability = opportunity.get(
            "ability",
            "",
        )

        key = (
            opportunity_type,
            timestamp,
            previous_ability,
            next_ability,
            ability,
        )

        if key in unique:
            continue

        unique[key] = True
        result.append(opportunity)

    return result


# ============================================================
# TERMINAL OUTPUT
# ============================================================

def format_opportunities(
    opportunities,
):
    """
    Format detected opportunities for terminal output.
    """

    print()
    print(
        "CONTEXTUAL IMPROVEMENT ANALYSIS"
    )
    print()

    print(
        f"Potential opportunities: "
        f"{len(opportunities)}"
    )

    if not opportunities:
        print()
        print(
            "No potential opportunities detected."
        )
        return

    for index, opportunity in enumerate(
        opportunities,
        start=1,
    ):
        print()

        opportunity_type = opportunity.get(
            "type",
            "UNKNOWN",
        )

        timestamp = opportunity.get(
            "timestamp",
            0,
        )

        severity = opportunity.get(
            "severity",
            "LOW",
        )

        gap_seconds = opportunity.get(
            "gap_seconds",
            0.0,
        )

        print(
            f"{index}. "
            f"[{severity}] "
            f"{timestamp / 1000:.2f}s | "
            f"{gap_seconds:.1f}s | "
            f"{opportunity_type}"
        )

        if opportunity_type == "CASTING_GAP":
            print(
                f"   Transition: "
                f"{opportunity.get('previous_ability', 'Unknown')} "
                f"-> "
                f"{opportunity.get('next_ability', 'Unknown')}"
            )

            context = opportunity.get(
                "context",
                {},
            )

            print(
                f"   Previous category: "
                f"{context.get('previous', 'unknown')}"
            )

            print(
                f"   Next category: "
                f"{context.get('next', 'unknown')}"
            )

        elif opportunity_type == "DOT_GAP":
            print(
                f"   Ability: "
                f"{opportunity.get('ability', 'Unknown')}"
            )

        print(
            f"   Classification: "
            f"{opportunity.get('classification', 'UNKNOWN')}"
        )

        print(
            f"   Confidence: "
            f"{opportunity.get('confidence', 'UNKNOWN')}"
        )

        print(
            f"   Evidence: "
            f"{opportunity.get('evidence', '')}"
        )

        print(
            f"   Damage events: "
            f"{opportunity.get('damage_events', 0)}"
        )

        print(
            f"   Effect events: "
            f"{opportunity.get('effect_events', 0)}"
        )