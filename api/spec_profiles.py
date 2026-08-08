"""
Spec profiles for DaddyAnalyzer.

The analysis engine should remain class/spec agnostic.
Spec-specific abilities and rules live here.
"""

SPEC_PROFILES = {

    # ============================================================
    # BALANCE DRUID
    # ============================================================

    "balance_druid": {
        "class": "Druid",
        "spec": "Balance",

        "abilities": {
            # Core damage
            "Moonfire": {
   		 "category": "dot",
   		 "role": "damage",
    		 "track_uptime": True,
   		 "track_targets": True,
   		 "track_refreshes": True,

   		 "opportunity_rules": {
      		   "use_temporal_coverage": True,
     		   "full_coverage_is_normal": True,
      		   "partial_coverage_is_potential": True,
       	 	   "none_coverage_is_potential": True,
      		   "unknown_coverage_is_inconclusive": True,
    		},
	   },

            "Sunfire": {
    		"category": "dot",
    		"role": "damage",
    		"track_uptime": True,
   		"track_targets": True,
    		"track_refreshes": True,

    		"opportunity_rules": {
        	  "use_temporal_coverage": True,
        	  "full_coverage_is_normal": True,
        	  "partial_coverage_is_potential": True,
        	  "none_coverage_is_potential": True,
        	  "unknown_coverage_is_inconclusive": True,
   		  },
	   },

            "Starfire": {
                "category": "builder",
                "role": "damage",
                "castable_during": [
                    "Eclipse (Solar)",
                    "Incarnation: Chosen of Elune",
                ],
            },

            "Wrath": {
                "category": "builder",
                "role": "damage",
                "castable_during": [
                    "Eclipse (Lunar)",
                    "Incarnation: Chosen of Elune",
                ],
            },

            "Starsurge": {
                "category": "spender",
                "role": "damage",
                "track_usage": True,
                "track_timing": True,
            },

            "Starfall": {
                "category": "spender",
                "role": "damage",
                "track_usage": True,
                "track_aoe": True,
                "track_timing": True,
            },

            # Cooldowns
            "Incarnation: Chosen of Elune": {
                "category": "cooldown",
                "role": "damage",
                "track_usage": True,
                "track_alignment": True,
            },

            "Fury of Elune": {
                "category": "cooldown",
                "role": "damage",
                "track_usage": True,
                "track_alignment": True,
            },

            "Solar Beam": {
                "category": "utility",
                "role": "interrupt",
                "track_usage": True,
            },

            "Stampeding Roar": {
                "category": "utility",
                "role": "movement",
                "track_usage": True,
            },

            "Wild Charge": {
                "category": "utility",
                "role": "movement",
                "track_usage": True,
            },

            "Barkskin": {
                "category": "defensive",
                "role": "survival",
                "track_usage": True,
            },

            # Forms
            "Moonkin Form": {
                "category": "form",
                "role": "stance",
                "track_usage": True,
            },

            "Travel Form": {
                "category": "movement",
                "role": "movement",
                "track_usage": True,
            },

            "Cat Form": {
                "category": "form",
                "role": "movement",
                "track_usage": True,
            },

            "Bear Form": {
                "category": "defensive",
                "role": "survival",
                "track_usage": True,
            },

            # Buffs / effects
            "Eclipse (Lunar)": {
                "category": "buff",
                "role": "damage_window",
                "track_duration": True,
                "track_alignment": True,
            },

            "Eclipse (Solar)": {
                "category": "buff",
                "role": "damage_window",
                "track_duration": True,
                "track_alignment": True,
            },

            "Balance of All Things": {
                "category": "buff",
                "role": "damage_window",
                "track_stacks": True,
                "track_duration": True,
            },

            "Solstice": {
                "category": "buff",
                "role": "damage_window",
                "track_duration": True,
            },

            "Starlord": {
                "category": "buff",
                "role": "damage_window",
                "track_stacks": True,
                "track_duration": True,
            },

            "Starfall": {
                "category": "spender",
                "role": "damage",
                "track_usage": True,
                "track_aoe": True,
                "track_timing": True,
            },
        },

        "dot_abilities": [
            "Moonfire",
            "Sunfire",
        ],

        "builder_abilities": [
            "Starfire",
            "Wrath",
        ],

        "spender_abilities": [
            "Starsurge",
            "Starfall",
        ],

        "cooldown_abilities": [
            "Incarnation: Chosen of Elune",
            "Fury of Elune",
        ],

        "defensive_abilities": [
            "Barkskin",
            "Bear Form",
        ],

        "utility_abilities": [
            "Solar Beam",
            "Stampeding Roar",
            "Wild Charge",
            "Remove Corruption",
        ],

        "movement_abilities": [
            "Travel Form",
            "Wild Charge",
            "Dash",
            "Stampeding Roar",
        ],

        "important_effects": [
            "Eclipse (Lunar)",
            "Eclipse (Solar)",
            "Balance of All Things",
            "Solstice",
            "Starlord",
            "Incarnation: Chosen of Elune",
            "Fury of Elune",
        ],
    },


    # ============================================================
    # GENERIC FALLBACK
    # ============================================================

    "unknown": {
        "class": "Unknown",
        "spec": "Unknown",

        "abilities": {},

        "dot_abilities": [],
        "builder_abilities": [],
        "spender_abilities": [],
        "cooldown_abilities": [],
        "defensive_abilities": [],
        "utility_abilities": [],
        "movement_abilities": [],
        "important_effects": [],
    },
}


def get_spec_profile(class_name, spec_name):
    """
    Return the profile for a class/spec combination.

    Example:
        get_spec_profile("Druid", "Balance")
    """

    if not class_name or not spec_name:
        return SPEC_PROFILES["unknown"]

    key = f"{spec_name.lower()}_{class_name.lower()}"

    return SPEC_PROFILES.get(
        key,
        SPEC_PROFILES["unknown"],
    )


def get_ability_profile(class_name, spec_name, ability_name):
    """
    Return the profile for a specific ability.
    """

    profile = get_spec_profile(
        class_name,
        spec_name,
    )

    return profile["abilities"].get(
        ability_name
    )


def is_known_ability(class_name, spec_name, ability_name):
    """
    Check whether an ability exists in the selected spec profile.
    """

    return (
        get_ability_profile(
            class_name,
            spec_name,
            ability_name,
        )
        is not None
    )


def get_abilities_by_category(
    class_name,
    spec_name,
    category,
):
    """
    Return all abilities belonging to a category.
    """

    profile = get_spec_profile(
        class_name,
        spec_name,
    )

    return {
        name: data
        for name, data in profile["abilities"].items()
        if data.get("category") == category
    }