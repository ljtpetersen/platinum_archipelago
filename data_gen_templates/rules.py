# data_gen_templates/rules.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import CollectionState
from collections.abc import Callable, Mapping, MutableMapping
from . import Hm, items, locations, species

Rule = Callable[[CollectionState], bool]

def create_hm_badge_rule(hm: Hm, player: int) -> Rule:
    badge_item = hm.badge_item()
    if badge_item:
        def hm_badge_rule(state: CollectionState) -> bool:
            return state.has(badge_item, player)
    else:
        def hm_badge_rule(state: CollectionState) -> bool:
            return True
    return hm_badge_rule

class Rules:
    exit_rules: Mapping[str, Rule]
    location_rules: Mapping[str, Rule]
    common_rules: MutableMapping[str, Callable]
    
    def __init__(self, player: int, common_rules: MutableMapping[str, Callable]):
        self.player = player
        self.common_rules = common_rules
        self.common_rules.update({ hm.name.lower():self.create_hm_rule(hm, player) for hm in Hm })
        def regional_mons(n: int) -> Rule:
            mons = [f"mon_{spec}" for spec in species.regional_mons]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(mons, player, n)
            return rule
        def mons(n: int) -> Rule:
            mons = [f"mon_{spec}" for spec in species.species.keys()]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(mons, player, n)
            return rule
        def badges(n: int) -> Rule:
            badges = [items.items[loc.original_item].label
                for loc in locations.locations.values() if loc.type == "badge"]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(badges, player, n)
            return rule
        self.common_rules["regional_mons"] = regional_mons
        self.common_rules["mons"] = mons
        self.common_rules["badges"] = badges

    def fill_rules(self):
        self.common_rules.update({
            # TEMPLATE: COMMON_RULES
        })
        self.exit_rules = {
            # TEMPLATE: EXIT_RULES
        }
        self.location_rules = {
            # TEMPLATE: LOCATION_RULES
        }

    def create_hm_rule(self, hm: Hm, player: int) -> Rule:
        mons = set()
        item_evols = []
        for name, spec in species.species.items():
            if hm not in spec.hms:
                continue
            mons.add(f"mon_{name}")
            while spec.pre_evolution:
                new_spec = species.species[spec.pre_evolution.species]
                if hm in new_spec.hms:
                    break
                if spec.pre_evolution.item:
                    item_evols.append([f"mon_{spec.pre_evolution.species}", spec.pre_evolution.item])
                else:
                    mons.add(f"mon_{spec.pre_evolution.species}")
                spec = new_spec

        def hm_rule(state: CollectionState) -> bool:
            if not (state.has(hm, player) and self.common_rules[f"{hm.name.lower()}_badge"](state)):
                return False
            if state.has_any(mons, player):
                return True
            for item_evol in item_evols:
                if state.has_all(item_evol, player):
                    return True
            return False

        return hm_rule
