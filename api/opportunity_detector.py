# V12 - FINAL-STATE-AWARE TEMPORAL COVERAGE
# V11 - TARGET-AWARE TEMPORAL COVERAGE WITH FINAL TARGET STATE
"""
DaddyAnalyzer - Opportunity Detector V9

Spec-agnostic combat opportunity detection with target temporal coverage.

Important:
- Does not automatically call gameplay mistakes "mistakes".
- Uses spec_profiles.py for spec-specific ability categories.
- Uses Warcraft Logs outgoing effects for target-aware DoT analysis.
- Target state is evidence, not a final gameplay judgement.
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
    outgoing_effects=None,
):
    profile = get_spec_profile(
        class_name,
        spec_name,
    )

    casts = casts or []
    effects = effects or []
    damage_events = damage_events or []
    outgoing_effects = outgoing_effects or []

    if not casts:
        return []

    dot_abilities = set(
        profile.get("dot_abilities", [])
    )

    builder_abilities = set(
        profile.get("builder_abilities", [])
    )

    spender_abilities = set(
        profile.get("spender_abilities", [])
    )

    cooldown_abilities = set(
        profile.get("cooldown_abilities", [])
    )

    ability_profiles = profile.get(
        "abilities",
        {},
    )

    damage_abilities = {
        name
        for name, data in ability_profiles.items()
        if data.get("role") == "damage"
    }

    normalized_casts = [
        cast
        for cast in casts
        if cast.get("timestamp") is not None
    ]

    normalized_casts.sort(
        key=lambda event: event["timestamp"]
    )

    relevant_casts = [
        cast
        for cast in normalized_casts
        if cast.get("ability_name")
        in damage_abilities
    ]

    opportunities = []

    opportunities.extend(
        _detect_casting_gaps(
            relevant_casts=relevant_casts,
            effects=effects,
            damage_events=damage_events,
            dot_abilities=dot_abilities,
            builder_abilities=builder_abilities,
            spender_abilities=spender_abilities,
            cooldown_abilities=cooldown_abilities,
        )
    )

    opportunities.extend(
        _detect_ability_specific_opportunities(
            casts=normalized_casts,
            effects=effects,
            damage_events=damage_events,
            outgoing_effects=outgoing_effects,
            profile=profile,
        )
    )

    opportunities = _deduplicate_opportunities(
        opportunities
    )

    opportunities.sort(
        key=lambda opportunity: (
            opportunity.get("timestamp", 0),
            opportunity.get("type", ""),
        )
    )

    return opportunities


# ============================================================
# CASTING GAP ANALYSIS
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

        gap_seconds = (
            next_time - previous_time
        ) / 1000.0

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

        classification = _classify_gap(
            damage_during_gap,
            effects_during_gap,
        )

        confidence = _calculate_confidence(
            gap_seconds,
            classification,
            len(damage_during_gap),
            len(effects_during_gap),
        )

        severity = _calculate_severity(
            gap_seconds,
            classification,
            confidence,
        )

        opportunities.append(
            {
                "type": "CASTING_GAP",
                "timestamp": previous_time,
                "gap_seconds": gap_seconds,
                "previous_ability": previous_cast.get(
                    "ability_name",
                    "Unknown",
                ),
                "next_ability": next_cast.get(
                    "ability_name",
                    "Unknown",
                ),
                "severity": severity,
                "classification": classification,
                "confidence": confidence,
                "evidence": _build_gap_evidence(
                    classification,
                    len(damage_during_gap),
                    len(effects_during_gap),
                ),
                "damage_events": len(
                    damage_during_gap
                ),
                "effect_events": len(
                    effects_during_gap
                ),
                "context": _build_ability_context(
                    previous_cast.get(
                        "ability_name",
                        "Unknown",
                    ),
                    next_cast.get(
                        "ability_name",
                        "Unknown",
                    ),
                    dot_abilities,
                    builder_abilities,
                    spender_abilities,
                    cooldown_abilities,
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
    outgoing_effects,
    profile,
):
    opportunities = []

    abilities = profile.get(
        "abilities",
        {},
    )

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
    # DOT GAPS
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

        ability_casts.sort(
            key=lambda event: event["timestamp"]
        )

    # ----------------------------------------------------
    # STAR SURGE SPENDER ANALYSIS
    # ----------------------------------------------------

    if ability_name == "Starsurge":
        opportunities.append(
            {
                "type": "STAR_SURGE_ANALYSIS",
                "timestamp": current_time,
                "gap_seconds": gap_seconds,
                "ability": ability_name,
                "severity": "LOW",
                "classification": "SPENDER TIMING",
                "confidence": "LOW",
                "score": 0,
                "evidence": (
                    f"{ability_name} had a {gap_seconds:.1f}s interval between casts."
                ),
                "damage_events": len(damage_during_gap),
                "effect_events": len(effects_during_gap),
                "target_state": target_state,
                "next_analysis": "RESOURCE / ECLIPSE / TARGET / BUFF STATE",
            }
        )

        for index in range(
            len(ability_casts) - 1
        ):
            current_cast = ability_casts[index]
            next_cast = ability_casts[index + 1]

            current_time = current_cast["timestamp"]
            next_time = next_cast["timestamp"]

            gap_seconds = (
                next_time - current_time
            ) / 1000.0

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

            target_state = analyze_target_state(
                outgoing_effects=outgoing_effects,
                ability_name=ability_name,
                start_time=current_time,
                end_time=next_time,
            )

            dot_classification, dot_confidence, dot_severity, dot_score = (
                _classify_dot_opportunity(
                    gap_seconds=gap_seconds,
                    target_state=target_state,
                    damage_events=len(damage_during_gap),
                    effect_events=len(effects_during_gap),
                opportunity_rules=ability_data.get(
                    "opportunity_rules",
                    {},
                ),
                )
            )

            coverage_summary = target_state.get(
                "coverage_summary",
                {},
            )
    
            target_scope = (
                "MULTI_TARGET"
                if ability_data.get("track_targets", False)
                else "SINGLE_TARGET"
            )
    
            target_summary = {
                "scope": target_scope,
                "target_count": target_state.get("target_count", 0),
                "active_targets_before_gap": len(
                    target_state.get("active_targets_before_gap", [])
                ),
                "targets_during_gap": len(
                    target_state.get("targets_during_gap", [])
                ),
                "coverage": {
                    "FULL": coverage_summary.get("full", 0),
                    "PARTIAL": coverage_summary.get("partial", 0),
                    "NONE": coverage_summary.get("none", 0),
                    "UNKNOWN": coverage_summary.get("unknown", 0),
                },
                "applications": target_state.get("applications_during_gap", 0),
                "refreshes": target_state.get("refreshes_during_gap", 0),
                "removals": target_state.get("removals_during_gap", 0),
            }
    
            opportunities.append(
                {
                    "type": "DOT_GAP",
                    "timestamp": current_time,
                    "gap_seconds": gap_seconds,
                    "ability": ability_name,
                    "severity": dot_severity,
                    "classification": dot_classification,
                    "confidence": dot_confidence,
                    "score": dot_score,
                                "target_summary": target_summary,
                    "evidence": _build_dot_evidence(
                        ability_name=ability_name,
                        gap_seconds=gap_seconds,
                        target_state=target_state,
                    ),
                    "damage_events": len(
                        damage_during_gap
                    ),
                    "effect_events": len(
                        effects_during_gap
                    ),
                    "target_state": target_state,
                }
            )

    # --------------------------------------------------------
    # ABILITY TRANSITIONS
    # --------------------------------------------------------

    for index in range(
        len(casts) - 1
    ):
        previous_cast = casts[index]
        next_cast = casts[index + 1]

        previous_ability = previous_cast.get(
            "ability_name"
        )

        next_ability = next_cast.get(
            "ability_name"
        )

        if not previous_ability:
            continue

        if not next_ability:
            continue

        previous_time = previous_cast["timestamp"]
        next_time = next_cast["timestamp"]

        gap_seconds = (
            next_time - previous_time
        ) / 1000.0

        if gap_seconds < 8.0:
            continue

        previous_category = _get_ability_category(
            previous_ability,
            dot_abilities,
            builder_abilities,
            spender_abilities,
            cooldown_abilities,
        )

        next_category = _get_ability_category(
            next_ability,
            dot_abilities,
            builder_abilities,
            spender_abilities,
            cooldown_abilities,
        )

        # ----------------------------------------------------
        # DOT -> DOT
        # ----------------------------------------------------

        if (
            previous_category == "dot"
            and next_category == "dot"
            and previous_ability != next_ability
        ):

            target_state = analyze_target_state(
                outgoing_effects=outgoing_effects,
                ability_name=next_ability,
                start_time=previous_time,
                end_time=next_time,
            )

            opportunities.append(
                {
                    "type": "DOT_SPECIFIC",
                    "timestamp": previous_time,
                    "gap_seconds": gap_seconds,
                    "previous_ability": previous_ability,
                    "next_ability": next_ability,
                    "ability": next_ability,
                    "transition": "DOT_TO_DOT",
                    "severity": "LOW",
                    "classification": (
                        "DOT PRIORITY DECISION"
                    ),
                    "confidence": target_state[
                        "confidence"
                    ],
                    "evidence": (
                        _build_transition_evidence(
                            previous_ability,
                            next_ability,
                            gap_seconds,
                            target_state,
                        )
                    ),
                    "damage_events": len(
                        _events_between(
                            damage_events,
                            previous_time,
                            next_time,
                        )
                    ),
                    "effect_events": len(
                        _events_between(
                            effects,
                            previous_time,
                            next_time,
                        )
                    ),
                    "target_state": target_state,
                    "next_analysis": (
                        "TARGET / REFRESH / "
                        "DOT DURATION / AURA STATE"
                    ),
                }
            )

        # ----------------------------------------------------
        # SPENDER -> BUILDER
        # ----------------------------------------------------

        elif (
            previous_category == "spender"
            and next_category == "builder"
        ):

            opportunities.append(
                {
                    "type": "ABILITY_SPECIFIC",
                    "timestamp": previous_time,
                    "gap_seconds": gap_seconds,
                    "previous_ability": previous_ability,
                    "next_ability": next_ability,
                    "transition": (
                        "SPENDER_TO_BUILDER"
                    ),
                    "severity": "LOW",
                    "classification": (
                        "ABILITY DECISION POINT"
                    ),
                    "confidence": "LOW",
                    "evidence": (
                        f"{previous_ability} -> "
                        f"{next_ability} occurred across "
                        f"a {gap_seconds:.1f}s gap. "
                        "This is a candidate for "
                        "spender/builder timing analysis."
                    ),
                    "damage_events": len(
                        _events_between(
                            damage_events,
                            previous_time,
                            next_time,
                        )
                    ),
                    "effect_events": len(
                        _events_between(
                            effects,
                            previous_time,
                            next_time,
                        )
                    ),
                    "next_analysis": (
                        "RESOURCE / TARGET / BUFF STATE"
                    ),
                }
            )

        # ----------------------------------------------------
        # SPENDER -> DOT
        # ----------------------------------------------------

        elif (
            previous_category == "spender"
            and next_category == "dot"
        ):

            target_state = analyze_target_state(
                outgoing_effects=outgoing_effects,
                ability_name=next_ability,
                start_time=previous_time,
                end_time=next_time,
            )

            opportunities.append(
                {
                    "type": "ABILITY_SPECIFIC",
                    "timestamp": previous_time,
                    "gap_seconds": gap_seconds,
                    "previous_ability": previous_ability,
                    "next_ability": next_ability,
                    "transition": (
                        "SPENDER_TO_DOT"
                    ),
                    "severity": "LOW",
                    "classification": (
                        "ABILITY DECISION POINT"
                    ),
                    "confidence": target_state[
                        "confidence"
                    ],
                    "evidence": (
                        f"{previous_ability} -> "
                        f"{next_ability} occurred across "
                        f"a {gap_seconds:.1f}s gap. "
                        "Target-state evidence is included "
                        "before judging DoT timing."
                    ),
                    "damage_events": len(
                        _events_between(
                            damage_events,
                            previous_time,
                            next_time,
                        )
                    ),
                    "effect_events": len(
                        _events_between(
                            effects,
                            previous_time,
                            next_time,
                        )
                    ),
                    "target_state": target_state,
                    "next_analysis": (
                        "RESOURCE / TARGET / BUFF STATE"
                    ),
                }
            )

        # ----------------------------------------------------
        # BUILDER -> DOT
        # ----------------------------------------------------

        elif (
            previous_category == "builder"
            and next_category == "dot"
        ):

            target_state = analyze_target_state(
                outgoing_effects=outgoing_effects,
                ability_name=next_ability,
                start_time=previous_time,
                end_time=next_time,
            )

            opportunities.append(
                {
                    "type": "ABILITY_SPECIFIC",
                    "timestamp": previous_time,
                    "gap_seconds": gap_seconds,
                    "previous_ability": previous_ability,
                    "next_ability": next_ability,
                    "transition": (
                        "BUILDER_TO_DOT"
                    ),
                    "severity": "LOW",
                    "classification": (
                        "DOT TIMING DECISION"
                    ),
                    "confidence": target_state[
                        "confidence"
                    ],
                    "evidence": (
                        f"{previous_ability} -> "
                        f"{next_ability} occurred across "
                        f"a {gap_seconds:.1f}s gap. "
                        "Target-state evidence is included."
                    ),
                    "damage_events": len(
                        _events_between(
                            damage_events,
                            previous_time,
                            next_time,
                        )
                    ),
                    "effect_events": len(
                        _events_between(
                            effects,
                            previous_time,
                            next_time,
                        )
                    ),
                    "target_state": target_state,
                    "next_analysis": (
                        "RESOURCE / TARGET / BUFF STATE"
                    ),
                }
            )

    return opportunities


# ============================================================
# TARGET STATE
# ============================================================

def analyze_target_state(
    outgoing_effects,
    ability_name,
    start_time,
    end_time,
):
    """
    Reconstruct observable DoT state per target and calculate
    target-specific temporal coverage inside the gap.

    Temporal rules:
        - applydebuff / refreshdebuff starts or extends observable coverage.
        - removedebuff closes observable coverage.
        - removedebuffstack only changes stack count and does NOT close
          observable coverage; the aura remains active until an explicit
          removedebuff event is observed.
        - No fixed DoT duration is assumed.
        - An interval still open at end_time is UNKNOWN beyond the last
          explicit aura event; it is not silently treated as expired.
        - Coverage is calculated by overlap with [start_time, end_time].
        - Final state is evaluated after all gap events, so a removal
          followed by apply/refresh is not classified as removal-only.
    """

    empty_result = {
        "target_data_available": False,
        "_gap_start": start_time,
        "_gap_end": end_time,
        "targets": [],
        "targets_before_gap": [],
        "targets_during_gap": [],
        "applications_during_gap": 0,
        "refreshes_during_gap": 0,
        "removals_during_gap": 0,
        "active_targets_before_gap": [],
        "removed_targets_during_gap": [],
        "target_states": {},
        "target_diagnostics": {},
        "temporal_coverage": {},
        "coverage_summary": {
            "full": 0,
            "partial": 0,
            "none": 0,
            "unknown": 0,
        },
        "target_count": 0,
        "confidence": "LOW",
        "state": "TARGET DATA UNAVAILABLE",
    }

    if not outgoing_effects:
        return empty_result

    relevant = [
        event
        for event in outgoing_effects
        if (
            event.get("ability_name") == ability_name
            and event.get("timestamp") is not None
            and event.get("target_id") is not None
        )
    ]

    if not relevant:
        empty_result["state"] = "NO TARGET EVENTS"
        return empty_result

    relevant.sort(key=lambda event: event["timestamp"])

    def get_target_key(event):
        target_id = event.get("target_id")
        target_instance = event.get("target_instance")
        if target_instance is not None:
            return target_id, target_instance
        return target_id, None

    def target_display(target_key):
        target_id, target_instance = target_key
        if target_instance is not None:
            return f"{target_id}:{target_instance}"
        return target_id

    target_states = {}
    all_targets = set()
    targets_before_gap = set()
    targets_during_gap = set()
    applications_during_gap = 0
    refreshes_during_gap = 0
    removals_during_gap = 0

    for event in relevant:
        timestamp = event["timestamp"]
        if timestamp > end_time:
            continue

        target_key = get_target_key(event)
        event_type = event.get("type", "")
        all_targets.add(target_key)

        if target_key not in target_states:
            target_states[target_key] = {
                "target_id": event.get("target_id"),
                "target_instance": event.get("target_instance"),
                "active_at_gap_start": False,
                "active_at_end_of_gap": False,
                "last_event_before_gap": None,
                "last_timestamp_before_gap": None,
                "last_event_during_gap": None,
                "last_timestamp_during_gap": None,
                "last_apply": None,
                "last_refresh": None,
                "last_remove": None,
                "applications": 0,
                "refreshes": 0,
                "removals": 0,
                "stack_removals": 0,
                "stack_removals_during_gap": 0,
                "applied_during_gap": False,
                "final_state": "UNKNOWN",
                "refreshed_during_gap": False,
                "removed_during_gap": False,
                "events_before_gap": 0,
                "events_during_gap": 0,
                "_active_since": None,
                "_intervals": [],
            }

        state = target_states[target_key]

        if timestamp < start_time:
            targets_before_gap.add(target_key)
            state["events_before_gap"] += 1

            if event_type in {"applydebuff", "refreshdebuff"}:
                state["active_at_gap_start"] = True
                state["_active_since"] = timestamp
                state["last_apply"] = timestamp if event_type == "applydebuff" else state["last_apply"]
                state["last_refresh"] = timestamp if event_type == "refreshdebuff" else state["last_refresh"]
                if event_type == "applydebuff":
                    state["applications"] += 1
                else:
                    state["refreshes"] += 1
            elif event_type == "removedebuff":
                if state["_active_since"] is not None:
                    state["_intervals"].append((state["_active_since"], timestamp, True))
                state["_active_since"] = None
                state["active_at_gap_start"] = False
                state["last_remove"] = timestamp
                state["removals"] += 1
            elif event_type == "removedebuffstack":
                # A stack removal is not equivalent to removing the aura.
                # DoT temporal coverage therefore remains active unless an
                # explicit removedebuff event is observed.
                state["stack_removals"] += 1

            state["last_event_before_gap"] = event_type
            state["last_timestamp_before_gap"] = timestamp
            continue

        if start_time <= timestamp <= end_time:
            targets_during_gap.add(target_key)
            state["events_during_gap"] += 1

            if event_type in {"applydebuff", "refreshdebuff"}:
                if event_type == "applydebuff":
                    applications_during_gap += 1
                    state["applications"] += 1
                    state["applied_during_gap"] = True
                    state["last_apply"] = timestamp
                else:
                    refreshes_during_gap += 1
                    state["refreshes"] += 1
                    state["refreshed_during_gap"] = True
                    state["last_refresh"] = timestamp

                if state["_active_since"] is not None:
                    state["_intervals"].append((state["_active_since"], timestamp, True))
                state["_active_since"] = timestamp
                state["active_at_end_of_gap"] = True

            elif event_type == "removedebuff":
                removals_during_gap += 1
                state["removals"] += 1
                state["removed_during_gap"] = True
                state["last_remove"] = timestamp

                if state["_active_since"] is not None:
                    state["_intervals"].append((state["_active_since"], timestamp, True))
                state["_active_since"] = None
                state["active_at_end_of_gap"] = False

            elif event_type == "removedebuffstack":
                # Stack loss is diagnostic evidence only. It does not end
                # aura/DoT coverage because the debuff can remain active
                # with fewer stacks.
                state["stack_removals"] += 1
                state["stack_removals_during_gap"] += 1

            state["last_event_during_gap"] = event_type
            state["last_timestamp_during_gap"] = timestamp

    # ------------------------------------------------------------
    # FINAL TARGET STATE
    # ------------------------------------------------------------
    # Events during the gap can include a removal followed by a new
    # application/refresh. "removed_during_gap" alone is therefore
    # not sufficient to describe how the target ended.
    for target_key, state in target_states.items():
        if state["active_at_end_of_gap"]:
            if state["applied_during_gap"] and state["removed_during_gap"]:
                state["final_state"] = "ACTIVE_REESTABLISHED"
            elif state["refreshed_during_gap"] and state["removed_during_gap"]:
                state["final_state"] = "ACTIVE_REFRESHED"
            elif state["applied_during_gap"]:
                state["final_state"] = "ACTIVE_APPLIED"
            elif state["refreshed_during_gap"]:
                state["final_state"] = "ACTIVE_REFRESHED"
            elif state["active_at_gap_start"]:
                state["final_state"] = "ACTIVE_UNCHANGED"
            else:
                state["final_state"] = "ACTIVE"
        elif state["removed_during_gap"]:
            state["final_state"] = "REMOVED_ONLY"
        else:
            state["final_state"] = "INACTIVE"

    active_targets_before_gap = []
    removed_targets_during_gap = []
    temporal_coverage = {}
    coverage_summary = {"full": 0, "partial": 0, "none": 0, "unknown": 0}

    gap_duration_ms = max(0, end_time - start_time)

    for target_key, state in target_states.items():
        if state["active_at_gap_start"]:
            active_targets_before_gap.append(target_key)

        if state["removed_during_gap"]:
            removed_targets_during_gap.append(target_key)

        # Close any interval that remains open at the end of the observable window.
        open_at_end = state["_active_since"] is not None
        intervals = list(state["_intervals"])
        if open_at_end:
            intervals.append((state["_active_since"], end_time, False))
            state["active_at_end_of_gap"] = True

        clipped_intervals = []
        observed_coverage_ms = 0
        explicit_full_interval = False

        for interval_start, interval_end, explicitly_closed in intervals:
            overlap_start = max(start_time, interval_start)
            overlap_end = min(end_time, interval_end)
            if overlap_end <= overlap_start:
                continue

            clipped_intervals.append({
                "start": overlap_start,
                "end": overlap_end,
                "duration_seconds": (overlap_end - overlap_start) / 1000.0,
                "explicit_end": bool(explicitly_closed),
            })
            observed_coverage_ms += overlap_end - overlap_start
            if overlap_start <= start_time and overlap_end >= end_time and explicitly_closed:
                explicit_full_interval = True

        # A fully observed interval requires explicit evidence at both ends.
        # An open interval is never promoted to FULL by a guessed DoT duration.
        if explicit_full_interval:
            coverage_state = "FULL"
        elif clipped_intervals and observed_coverage_ms > 0:
            if open_at_end:
                coverage_state = "UNKNOWN"
            else:
                coverage_state = "PARTIAL"
        else:
            coverage_state = "NONE"

        coverage_seconds = observed_coverage_ms / 1000.0
        coverage_ratio = (
            coverage_seconds / (gap_duration_ms / 1000.0)
            if gap_duration_ms > 0 else 0.0
        )

        temporal_coverage[target_display(target_key)] = {
            "target_id": state["target_id"],
            "target_instance": state["target_instance"],
            "coverage": coverage_state,
            "coverage_seconds": round(coverage_seconds, 3),
            "gap_seconds": round(gap_duration_ms / 1000.0, 3),
            "coverage_ratio": round(coverage_ratio, 4),
            "active_at_gap_start": bool(state["active_at_gap_start"]),
            "active_at_gap_end": bool(state["active_at_end_of_gap"]),
            "open_at_end": bool(open_at_end),
            "intervals": clipped_intervals,
        }

        coverage_summary[coverage_state.lower()] += 1

    def display_sorted(values):
        return sorted([target_display(key) for key in values], key=lambda value: str(value))

    targets = display_sorted(all_targets)
    targets_before = display_sorted(targets_before_gap)
    targets_during = display_sorted(targets_during_gap)
    active_before = display_sorted(active_targets_before_gap)
    removed_during = display_sorted(removed_targets_during_gap)

    target_diagnostics = {}
    for target_key in active_targets_before_gap:
        state = target_states[target_key]
        coverage = temporal_coverage.get(target_display(target_key), {})
        final_state = state.get("final_state", "UNKNOWN")

        if final_state == "REMOVED_ONLY":
            explained_by = "REMOVED_ONLY"
        elif final_state == "ACTIVE_REESTABLISHED":
            explained_by = "ACTIVE_REESTABLISHED"
        elif final_state == "ACTIVE_REFRESHED":
            explained_by = "ACTIVE_REFRESHED"
        elif final_state == "ACTIVE_APPLIED":
            explained_by = "ACTIVE_APPLIED"
        elif final_state == "ACTIVE_UNCHANGED":
            explained_by = "ACTIVE_UNCHANGED"
        elif final_state == "INACTIVE":
            explained_by = "INACTIVE"
        else:
            explained_by = "UNKNOWN"

        target_diagnostics[target_display(target_key)] = {
            "active_before_gap": True,
            "applied_during_gap": bool(state["applied_during_gap"]),
            "refreshed_during_gap": bool(state["refreshed_during_gap"]),
            "removed_during_gap": bool(state["removed_during_gap"]),
            "stack_removals_during_gap": int(state.get("stack_removals_during_gap", 0)),
            "final_state": state.get("final_state", "UNKNOWN"),
            "explained_by": explained_by,
            "temporal_coverage": coverage,
        }

    if removed_targets_during_gap:
        confidence = "MEDIUM"
        state_description = "TARGET EXPLICITLY REMOVED"
    elif active_targets_before_gap:
        confidence = "LOW"
        state_description = "ACTIVE TARGET COVERAGE OBSERVED"
    elif targets_during_gap:
        confidence = "LOW"
        state_description = "TARGET ACTIVITY DURING GAP"
    elif targets_before_gap:
        confidence = "LOW"
        state_description = "PREVIOUS TARGET COVERAGE OBSERVED"
    else:
        confidence = "LOW"
        state_description = "TARGET ACTIVITY OBSERVED"

    final_state_summary = {}
    for state in target_states.values():
        final_state = state.get("final_state", "UNKNOWN")
        final_state_summary[final_state] = (
            final_state_summary.get(final_state, 0) + 1
        )

    return {
        "target_data_available": True,
        "_gap_start": start_time,
        "_gap_end": end_time,
        "targets": targets,
        "targets_before_gap": targets_before,
        "targets_during_gap": targets_during,
        "applications_during_gap": applications_during_gap,
        "refreshes_during_gap": refreshes_during_gap,
        "removals_during_gap": removals_during_gap,
        "stack_removals_during_gap": sum(
            state.get("stack_removals_during_gap", 0)
            for state in target_states.values()
        ),
        "active_targets_before_gap": active_before,
        "removed_targets_during_gap": removed_during,
        "target_states": {target_display(key): state for key, state in target_states.items()},
        "target_diagnostics": target_diagnostics,
        "final_state_summary": final_state_summary,
        "temporal_coverage": temporal_coverage,
        "coverage_summary": coverage_summary,
        "target_count": len(all_targets),
        "confidence": confidence,
        "state": state_description,
    }


# ============================================================
# TARGET-AWARE DOT CLASSIFICATION
# ============================================================

def _classify_dot_opportunity(
    gap_seconds,
    target_state,
    damage_events=0,
    effect_events=0,
    opportunity_rules=None,
):
    """
    Classify DoT uptime evidence conservatively.

    FULL:
        Explicit coverage spans the complete gap.

    PARTIAL:
        Only part of the gap is explicitly covered.

    NONE:
        No observable coverage for a target active at gap start.

    UNKNOWN:
        Coverage remains open at the end of the observable window.
        Expiration cannot be inferred.
    """

    rules = opportunity_rules or {}

    if not rules.get("use_temporal_coverage", True):
        return (
            "TEMPORAL COVERAGE NOT TRACKED",
            "LOW",
            "LOW",
            0,
        )

    if not target_state.get("target_data_available", False):
        return (
            "TARGET DATA INSUFFICIENT",
            "LOW",
            "LOW",
            15,
        )

    temporal = target_state.get("temporal_coverage", {})
    active_targets = target_state.get(
        "active_targets_before_gap",
        [],
    )

    def coverage_for(target_key):
        data = temporal.get(target_key)

        if data is None:
            data = temporal.get(str(target_key), {})

        return data.get("coverage", "UNKNOWN")

    # No target was demonstrably active when the gap started.
    if not active_targets:
        applications = target_state.get(
            "applications_during_gap",
            0,
        )
        refreshes = target_state.get(
            "refreshes_during_gap",
            0,
        )
        targets_during = len(
            target_state.get(
                "targets_during_gap",
                [],
            )
        )

        if applications or refreshes:
            score = 20

            if applications:
                score += 10

            if refreshes:
                score += 10

            return (
                "DOT ACTIVITY DURING GAP",
                "LOW",
                "LOW",
                min(score, 50),
            )

        if targets_during:
            score = 25

            if damage_events > 0:
                score += 5

            return (
                "TARGET ACTIVITY DURING GAP",
                "LOW",
                "LOW",
                min(score, 40),
            )

        return (
            "TARGET COVERAGE UNCERTAIN",
            "LOW",
            "LOW",
            20,
        )

    coverages = [
        coverage_for(target_key)
        for target_key in active_targets
    ]

    active_count = len(coverages)

    full_count = sum(
        coverage == "FULL"
        for coverage in coverages
    )

    partial_count = sum(
        coverage == "PARTIAL"
        for coverage in coverages
    )

    none_count = sum(
        coverage == "NONE"
        for coverage in coverages
    )

    unknown_count = sum(
        coverage == "UNKNOWN"
        for coverage in coverages
    )

    # --------------------------------------------------------
    # FULL = explicitly covered for the whole gap.
    # --------------------------------------------------------

    if full_count == active_count:
        score = 5

        if damage_events:
            score += 3

        if effect_events:
            score += 2

        return (
            "FULL TEMPORAL COVERAGE / LIKELY NORMAL",
            "LOW",
            "LOW",
            min(score, 20),
        )

    # --------------------------------------------------------
    # PARTIAL = possible uptime loss.
    # --------------------------------------------------------

    if partial_count:
        score = 35
        score += min(30, int(gap_seconds * 1.25))
        score += min(20, partial_count * 10)

        if full_count:
            score -= min(10, full_count * 3)

        if damage_events:
            score += 5

        if effect_events:
            score += 5

        score = max(20, min(score, 100))

        confidence = (
            "MEDIUM"
            if partial_count >= max(1, active_count // 2)
            else "LOW"
        )

        if not rules.get(
            "partial_coverage_is_potential",
            True,
        ):
            return (
                "PARTIAL DOT COVERAGE",
                "LOW",
                "LOW",
                min(score, 40),
            )

        if score >= 80:
            return (
                "STRONG POTENTIAL DOT UPTIME LOSS",
                confidence,
                "HIGH",
                score,
            )

        if score >= 60:
            return (
                "POTENTIAL DOT UPTIME LOSS",
                confidence,
                "MEDIUM",
                score,
            )

        return (
            "PARTIAL DOT COVERAGE GAP",
            "LOW",
            "LOW",
            score,
        )

    # --------------------------------------------------------
    # NONE = no observable coverage.
    # --------------------------------------------------------

    if none_count:
        score = 40
        score += min(30, int(gap_seconds * 1.25))
        score += min(20, none_count * 10)

        if unknown_count:
            score -= min(10, unknown_count * 3)

        if damage_events:
            score += 5

        if effect_events:
            score += 5

        score = max(25, min(score, 100))

        confidence = (
            "MEDIUM"
            if none_count >= max(1, active_count // 2)
            else "LOW"
        )

        if not rules.get(
            "none_coverage_is_potential",
            True,
        ):
            return (
                "NO TEMPORAL COVERAGE",
                "LOW",
                "LOW",
                min(score, 40),
            )

        if score >= 80:
            return (
                "STRONG POTENTIAL DOT UPTIME LOSS",
                confidence,
                "HIGH",
                score,
            )

        if score >= 60:
            return (
                "POTENTIAL DOT UPTIME LOSS",
                confidence,
                "MEDIUM",
                score,
            )

        return (
            "NO OBSERVABLE TEMPORAL COVERAGE",
            "LOW",
            "LOW",
            score,
        )

    # --------------------------------------------------------
    # UNKNOWN = never infer expiration.
    # --------------------------------------------------------

    if unknown_count:
        score = 20 + min(20, int(gap_seconds))

        if damage_events:
            score += 5

        if rules.get(
            "unknown_coverage_is_inconclusive",
            True,
        ):
            return (
                "TEMPORAL COVERAGE UNKNOWN",
                "LOW",
                "LOW",
                min(score, 45),
            )

        return (
            "TEMPORAL COVERAGE UNCERTAIN",
            "LOW",
            "LOW",
            min(score, 45),
        )

    return (
        "TARGET COVERAGE UNCERTAIN",
        "LOW",
        "LOW",
        20,
    )

# ============================================================
# EVIDENCE BUILDERS
# ============================================================

def _build_dot_evidence(
    ability_name,
    gap_seconds,
    target_state,
):
    if not target_state.get("target_data_available", False):
        return (
            f"{ability_name} had a {gap_seconds:.1f}s gap. "
            "Target-specific data was not available, so temporal DoT coverage "
            "cannot be established."
        )

    temporal = target_state.get("temporal_coverage", {})
    active_before = target_state.get(
        "active_targets_before_gap",
        [],
    )

    coverage_counts = {
        "FULL": 0,
        "PARTIAL": 0,
        "NONE": 0,
        "UNKNOWN": 0,
    }

    temporal_lines = []

    for target_key in active_before:
        data = temporal.get(target_key)

        if data is None:
            data = temporal.get(
                str(target_key),
                {},
            )

        coverage = data.get(
            "coverage",
            "UNKNOWN",
        )

        coverage_counts[coverage] = (
            coverage_counts.get(
                coverage,
                0,
            ) + 1
        )

        temporal_lines.append(
            f"{target_key}={coverage} "
            f"({data.get('coverage_seconds', 0.0):.1f}s/"
            f"{data.get('gap_seconds', gap_seconds):.1f}s)"
        )

    applications = target_state.get(
        "applications_during_gap",
        0,
    )

    refreshes = target_state.get(
        "refreshes_during_gap",
        0,
    )

    removals = target_state.get(
        "removals_during_gap",
        0,
    )

    target_count = target_state.get(
        "target_count",
        0,
    )

    target_scope = target_state.get(
        "target_summary",
        {},
    ).get(
        "scope",
        "SINGLE_TARGET",
    )

    targets_during = len(
        target_state.get(
            "targets_during_gap",
            [],
        )
    )

    final_state_summary = target_state.get(
        "final_state_summary",
        {},
    )

    temporal_text = (
        "; ".join(temporal_lines)
        if temporal_lines
        else "none at gap start"
    )

    return (
        f"{ability_name} had a {gap_seconds:.1f}s gap. "
        f"Target scope: {target_scope}. "
        f"{target_count} unique target(s) were observed; "
        f"{len(active_before)} were active at gap start and "
        f"{targets_during} were observed during the gap. "
        f"Temporal coverage: "
        f"FULL={coverage_counts['FULL']}, "
        f"PARTIAL={coverage_counts['PARTIAL']}, "
        f"NONE={coverage_counts['NONE']}, "
        f"UNKNOWN={coverage_counts['UNKNOWN']}. "
        f"Per-target: {temporal_text}. "
        f"Applications: {applications}. "
        f"Refreshes: {refreshes}. "
        f"Removals: {removals}. "
        f"Final target states: {final_state_summary}. "
        "No fixed DoT duration is assumed; "
        "an open interval remains UNKNOWN."
    )


def _build_transition_evidence(
    previous_ability,
    next_ability,
    gap_seconds,
    target_state,
):
    target_count = target_state.get(
        "target_count",
        0,
    )

    active_before = target_state.get(
        "active_targets_before_gap",
        [],
    )

    removed_during = target_state.get(
        "removed_targets_during_gap",
        [],
    )

    return (
        f"{previous_ability} -> "
        f"{next_ability} occurred across "
        f"a {gap_seconds:.1f}s gap. "
        f"{target_count} target(s) were observed "
        f"for {next_ability}. "
        f"{len(active_before)} target(s) had "
        "active coverage evidence at the start "
        "of the gap. "
        f"{len(removed_during)} target(s) had "
        "explicit removal evidence during the gap. "
        "Target-state evidence is included before "
        "judging DoT timing."
    )


def _build_gap_evidence(
    classification,
    damage_count,
    effect_count,
):
    if classification == "ONGOING DAMAGE":

        return (
            "Damage continued during the gap, "
            "so this is not confirmed downtime."
        )

    if classification == "COMBAT ACTIVITY":

        return (
            "Combat-related effects continued "
            "during the gap, so the player was "
            "not necessarily idle."
        )

    return (
        "No damage or effect events were detected "
        "during the gap between relevant casts."
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def _classify_gap(
    damage_during_gap,
    effects_during_gap,
):
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
    if classification == "POTENTIAL DOWNTIME":

        if gap_seconds >= 10.0:
            return "MEDIUM"

        return "LOW"

    if classification == "COMBAT ACTIVITY":
        return "LOW"

    return "LOW"


def _calculate_severity(
    gap_seconds,
    classification,
    confidence,
):
    if classification == "ONGOING DAMAGE":

        if gap_seconds >= 15.0:
            return "MEDIUM"

        return "LOW"

    if classification == "COMBAT ACTIVITY":
        return "LOW"

    if gap_seconds >= 10.0:
        return "MEDIUM"

    return "LOW"


# ============================================================
# ABILITY HELPERS
# ============================================================

def _build_ability_context(
    previous_ability,
    next_ability,
    dot_abilities,
    builder_abilities,
    spender_abilities,
    cooldown_abilities,
):
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
    unique = {}
    result = []

    for opportunity in opportunities:

        key = (
            opportunity.get(
                "type",
                "UNKNOWN",
            ),
            opportunity.get(
                "timestamp",
                0,
            ),
            opportunity.get(
                "previous_ability",
                "",
            ),
            opportunity.get(
                "next_ability",
                "",
            ),
            opportunity.get(
                "ability",
                "",
            ),
        )

        if key in unique:
            continue

        unique[key] = True
        result.append(
            opportunity
        )

    return result


# ============================================================
# OUTPUT FORMATTER
# ============================================================

def format_opportunities(
    opportunities,
):
    print()
    print(
        "ABILITY-SPECIFIC OPPORTUNITY ANALYSIS"
    )
    print()

    print(
        f"Potential opportunities: "
        f"{len(opportunities)}"
    )

    for index, opportunity in enumerate(
        opportunities,
        start=1,
    ):
        print()

        timestamp = opportunity.get(
            "timestamp",
            0,
        )

        gap_seconds = opportunity.get(
            "gap_seconds",
            0.0,
        )

        severity = opportunity.get(
            "severity",
            "LOW",
        )

        print(
            f"{index}. "
            f"[{severity}] "
            f"{timestamp / 1000:.2f}s | "
            f"{gap_seconds:.1f}s | "
            f"{_format_transition(opportunity)}"
        )

        print(
            f"   Type: "
            f"{opportunity.get('type', 'UNKNOWN')}"
        )

        if opportunity.get(
            "transition"
        ):
            print(
                f"   Transition: "
                f"{opportunity['transition']}"
            )

        if opportunity.get(
            "ability"
        ):
            print(
                f"   DoT: "
                f"{opportunity['ability']}"
            )

        print(
            f"   Classification: "
            f"{opportunity.get('classification', 'UNKNOWN')}"
        )

        print(
            f"   Confidence: "
            f"{opportunity.get('confidence', 'UNKNOWN')}"
        )

        if opportunity.get("score") is not None:
            print(
                f"   Score: "
                f"{opportunity.get('score')}/100"
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

        target_state = opportunity.get(
            "target_state"
        )

        if target_state:

            print(
                "   DoT evidence:"
            )

            print(
                f"   Target data: "
                f"{target_state.get('target_data_available', False)}"
            )

            print(
                f"   Targets: "
                f"{target_state.get('target_count', 0)}"
            )

            print(
                f"   Active targets before gap: "
                f"{len(target_state.get('active_targets_before_gap', []))}"
            )

            print(
                f"   Targets before gap: "
                f"{len(target_state.get('targets_before_gap', []))}"
            )

            print(
                f"   Targets during gap: "
                f"{len(target_state.get('targets_during_gap', []))}"
            )

            print(
                f"   Applications during gap: "
                f"{target_state.get('applications_during_gap', 0)}"
            )

            print(
                f"   Refreshes during gap: "
                f"{target_state.get('refreshes_during_gap', 0)}"
            )

            print(
                f"   Removals during gap: "
                f"{target_state.get('removals_during_gap', 0)}"
            )

            print(
                f"   Removed targets: "
                f"{target_state.get('removed_targets_during_gap', [])}"
            )
            print(
                f"   Stack removals during gap: "
                f"{target_state.get('stack_removals_during_gap', 0)}"
            )

            coverage_summary = target_state.get(
                "coverage_summary",
                {},
            )
            print(
                "   Temporal coverage: "
                f"FULL={coverage_summary.get('full', 0)} | "
                f"PARTIAL={coverage_summary.get('partial', 0)} | "
                f"UNKNOWN={coverage_summary.get('unknown', 0)} | "
                f"NONE={coverage_summary.get('none', 0)}"
            )

            temporal_coverage = target_state.get(
                "temporal_coverage",
                {},
            )
            if temporal_coverage:
                print("   Temporal target intervals:")
                for target_key in sorted(
                    temporal_coverage,
                    key=lambda value: str(value),
                ):
                    coverage = temporal_coverage[target_key]
                    print(
                        f"      Target {target_key}: "
                        f"coverage={coverage.get('coverage', 'UNKNOWN')} | "
                        f"covered={coverage.get('coverage_seconds', 0.0):.1f}s/"
                        f"{coverage.get('gap_seconds', 0.0):.1f}s | "
                        f"ratio={coverage.get('coverage_ratio', 0.0):.2f} | "
                        f"open_at_end={coverage.get('open_at_end', False)}"
                    )

            # ----------------------------------------------------
            # PER-TARGET DIAGNOSTICS
            # ----------------------------------------------------
            # Show exactly why every active target is considered
            # explained or unexplained. This is diagnostic only;
            # it does not change the scoring logic.
            active_targets = set(
                target_state.get(
                    "active_targets_before_gap",
                    [],
                )
            )

            target_states = target_state.get(
                "target_states",
                {},
            )

            if active_targets:
                print(
                    "   Per-target diagnostics:"
                )

                for target_key in sorted(
                    active_targets,
                    key=lambda value: str(value),
                ):
                    state = target_states.get(
                        target_key,
                        {},
                    )

                    applied = bool(
                        state.get(
                            "applied_during_gap",
                            False,
                        )
                    )

                    refreshed = bool(
                        state.get(
                            "refreshed_during_gap",
                            False,
                        )
                    )

                    removed = bool(
                        state.get(
                            "removed_during_gap",
                            False,
                        )
                    )

                    final_state = state.get(
                        "final_state",
                        "UNKNOWN",
                    )

                    # Final state is authoritative for the explanation.
                    # A target that was removed and then re-established is
                    # NOT explained by removal alone.
                    if final_state == "REMOVED_ONLY":
                        explained_by = "REMOVED_ONLY"
                    elif final_state == "ACTIVE_REESTABLISHED":
                        explained_by = "ACTIVE_REESTABLISHED"
                    elif final_state == "ACTIVE_REFRESHED":
                        explained_by = "ACTIVE_REFRESHED"
                    elif final_state == "ACTIVE_APPLIED":
                        explained_by = "ACTIVE_APPLIED"
                    elif final_state == "ACTIVE_UNCHANGED":
                        explained_by = "ACTIVE_UNCHANGED"
                    elif final_state == "INACTIVE":
                        explained_by = "INACTIVE"
                    else:
                        explained_by = "UNKNOWN"

                    print(
                        f"      Target {target_key}: "
                        f"active_before=YES | "
                        f"applied={applied} | "
                        f"refreshed={refreshed} | "
                        f"removed={removed} | "
                        f"final_state={final_state} | "
                        f"explained_by={explained_by}"
                    )

            print(
                f"   Target state: "
                f"{target_state.get('state', 'UNKNOWN')}"
            )

        if opportunity.get(
            "next_analysis"
        ):
            print(
                f"   Next analysis: "
                f"{opportunity['next_analysis']}"
            )


def _format_transition(
    opportunity,
):
    previous = opportunity.get(
        "previous_ability"
    )

    next_ability = opportunity.get(
        "next_ability"
    )

    if previous and next_ability:
        return (
            f"{previous} -> {next_ability}"
        )

    return opportunity.get(
        "ability",
        opportunity.get(
            "type",
            "UNKNOWN",
        ),
    )

