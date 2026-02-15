# data_gen_templates/rules.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from typing import Tuple, TYPE_CHECKING
from BaseClasses import CollectionState
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence

from . import Hm, items, locations, species

if TYPE_CHECKING:
    from ..options import PokemonPlatinumOptions

Rule = Callable[[CollectionState], bool]

def always_true(*args, **kwargs) -> bool:
    return True

def create_hm_badge_rule(hm: Hm, player: int) -> Rule:
    badge_item = hm.badge_item()
    if badge_item is not None:
        def hm_badge_rule(state: CollectionState) -> bool:
            return state.has(badge_item, player)
    else:
        def hm_badge_rule(state: CollectionState) -> bool:
            return True
    return hm_badge_rule

class Rules:
    exit_rules: Mapping[Tuple[str, str], Rule]
    location_rules: Mapping[str, Rule]
    encounter_type_rules: Mapping[str, Rule]
    location_type_rules: Mapping[str, Rule]
    common_rules: MutableMapping[str, Callable]
    trainer_rules: Mapping[str, Rule]
    opts: "PokemonPlatinumOptions"
    cached_enc_accessibility_rules: MutableMapping[frozenset[str], Rule]
    hm_mons: MutableMapping[Hm, MutableSequence[str]]
    
    def __init__(self, player: int, common_rules: MutableMapping[str, Callable], opts: "PokemonPlatinumOptions"):
        self.player = player
        self.opts = opts
        self.common_rules = common_rules
        self.cached_enc_accessibility_rules = {}
        self.hm_mons = {}
        def see_regional_mons(n: int) -> Rule:
            mons = [f"see_mon_{spec}" for spec in species.regional_mons]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(mons, player, n)
            return rule
        def see_mons(n: int) -> Rule:
            mons = [f"see_mon_{spec}" for spec in species.species.keys()]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(mons, player, n)
            return rule
        def badges(n: int) -> Rule:
            badges = [items.items[loc.original_item].label
                for loc in locations.locations.values() if loc.type == "badge"]
            def rule(state: CollectionState) -> bool:
                return state.has_from_list_unique(badges, player, n)
            return rule
        self.common_rules["see_regional_mons"] = see_regional_mons
        self.common_rules["see_mons"] = see_mons
        self.common_rules["badges"] = badges
        self.common_rules.update({f"use_{hm.name.lower()}":self.get_use_hm_rule(hm) for hm in Hm})

    def fill_rules(self):
        # TEMPLATE: COMMON_RULES
        self.exit_rules = {
            # TEMPLATE: EXIT_RULES
        }
        self.location_rules = {
            # TEMPLATE: LOCATION_RULES
        }
        self.location_type_rules = {
            # TEMPLATE: LOCATION_TYPE_RULES
        }
        self.encounter_type_rules = {
            # TEMPLATE: ENCOUNTER_TYPE_RULES
        }
        self.trainer_rules = {
            # TEMPLATE: TRAINER_RULES
        }

    def get_use_hm_rule(self, hm: Hm) -> Rule:
        if hm not in self.hm_mons:
            self.hm_mons[hm] = ["mon_" + mon for mon, data in species.species.items() if hm in data.hms]
        def rule(state: CollectionState) -> bool:
            return state.has_any(self.hm_mons[hm], self.player)
        return rule

    def get_enc_accessibility_rule(self, accessibility: Sequence[str]) -> Rule:
        nmd = frozenset(acc for acc in accessibility if acc in self.encounter_type_rules)
        if nmd in self.cached_enc_accessibility_rules:
            return self.cached_enc_accessibility_rules[nmd]
        rules = [self.encounter_type_rules[acc] for acc in accessibility if acc in self.encounter_type_rules]
        def rule(state: CollectionState) -> bool:
            for rule in rules:
                if rule(state):
                    return True
            return False
        self.cached_enc_accessibility_rules[nmd] = rule
        return rule

    def get_pevo_rule(self, pevo: species.PreEvolution, options: "PokemonPlatinumOptions") -> Rule | None:
        mthd = pevo.method
        reqd_items = [f"mon_{pevo.species}"]
        if mthd.startswith("trade"):
            reqd_items.append(items.items["linking_cord"].label)
        if mthd.endswith("day"):
            reqd_items.append(items.items["daytime"].label)
            reqd_items.append(items.items["poketch"].label)
        elif mthd.endswith("night"):
            reqd_items.append(items.items["nighttime"].label)
            reqd_items.append(items.items["poketch"].label)
        if pevo.item is not None:
            reqd_items.append(pevo.item)
            if (pevo.item not in items.reusable_evo_items or pevo.item.startswith("TM") and not options.reusable_tms) and not options.evo_items_shop_in_ap_helper:
                reqd_items.append("event_veilstone_store")
        elif pevo.other_species is not None:
            reqd_items.append(f"mon_{pevo.other_species}")
        if mthd == "level_magnetic_field":
            reqd_items.append("event_magnetic_field")
        elif mthd == "level_moss_rock":
            reqd_items.append("event_moss_rock")
        elif mthd == "level_ice_rock":
            reqd_items.append("event_ice_rock")

        def rule(state: CollectionState) -> bool:
            return state.has_all(reqd_items, self.player)
        return rule

    def get_mon_rule(self, mon: str) -> Rule:
        mon = f"mon_{mon}"
        def mon_rule(state: CollectionState) -> bool:
            return state.has(mon, self.player)
        return mon_rule

    def get_once_mon_rule(self, mon: str) -> Rule:
        mon = f"once_mon_{mon}"
        def mon_rule(state: CollectionState) -> bool:
            return state.has(mon, self.player)
        return mon_rule

    def get_roamer_rule(self, roamer: int) -> Rule:
        item = f"event_roamer_{roamer}"
        def roamer_rule(state: CollectionState) -> bool:
            return state.has(item, self.player)
        return roamer_rule
