# data_gen_templates/rules.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from typing import Tuple, TYPE_CHECKING
from BaseClasses import CollectionState
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from rule_builder.rules import Has, HasAll, HasAny, Rule, True_, False_, HasFromListUnique, Or, And
import operator

from . import Hm, items, locations, species

if TYPE_CHECKING:
    from ..options import PokemonPlatinumOptions

def create_hm_badge_rule(hm: Hm) -> Rule:
    badge_item = hm.badge_item()
    if badge_item is not None:
        return Has(badge_item)
    else:
        return True_()

class Rules:
    exit_rules: Mapping[Tuple[str, str], Rule]
    location_rules: Mapping[str, Rule]
    encounter_type_rules: Mapping[str, Rule]
    location_type_rules: Mapping[str, Rule]
    common_rules: MutableMapping[str, Callable[..., Rule] | Rule]
    trainer_rules: Mapping[str, Rule]
    opts: "PokemonPlatinumOptions"
    cached_enc_accessibility_rules: MutableMapping[frozenset[str], Rule]
    hm_mon_rules: MutableMapping[Hm, Rule]
    
    def __init__(self, common_rules: MutableMapping[str, Callable[..., Rule] | Rule], opts: "PokemonPlatinumOptions"):
        self.opts = opts
        self.common_rules = common_rules
        self.cached_enc_accessibility_rules = {}
        self.hm_mons = {}
        def see_regional_mons(n: int) -> Rule:
            return HasFromListUnique(*[f"see_mon_{spec}" for spec in species.regional_mons], count=n)
        def see_mons(n: int) -> Rule:
            return HasFromListUnique(*[f"see_mon_{spec}" for spec in species.species.keys()], count=n)
        def badges(n: int) -> Rule:
            badges = tuple(items.items[loc.original_item].label # type: ignore
                for loc in locations.locations.values() if loc.type == "badge")
            return HasFromListUnique(*badges, count=n)
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
        if self.opts.tmhm_compatibility > 0:
            return True_()
        if hm not in self.hm_mons:
            self.hm_mons[hm] = HasAny(*["mon_" + mon for mon, data in species.species.items() if hm in data.hms])
        return self.hm_mons[hm]

    def get_enc_accessibility_rule(self, accessibility: Sequence[str]) -> Rule:
        nmd = frozenset(acc for acc in accessibility if acc in self.encounter_type_rules)
        if nmd in self.cached_enc_accessibility_rules:
            return self.cached_enc_accessibility_rules[nmd]
        rule = Or(*[self.encounter_type_rules[acc] for acc in accessibility if acc in self.encounter_type_rules])
        self.cached_enc_accessibility_rules[nmd] = rule
        return rule

    def get_pevo_rule(self, pevo: species.PreEvolution, options: "PokemonPlatinumOptions") -> Rule | None:
        mthd = pevo.method
        reqd_items = [f"mon_{pevo.species}"]
        if mthd.startswith("trade"):
            reqd_items.extend([items.items["linking_cord"].label, items.items["bag"].label])
        if mthd.endswith("day"):
            reqd_items.extend([items.items["daytime"].label, items.items["poketch"].label])
        elif mthd.endswith("night"):
            reqd_items.extend([items.items["nighttime"].label, items.items["poketch"].label])
        if pevo.item is not None:
            reqd_items.append(pevo.item)
            if "held" not in mthd:
                reqd_items.append(items.items["bag"].label)
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
        if mthd in {"level_atk_gt_def", "level_atk_eq_def", "level_atk_lt_def"}:
            reqd_items.extend(["event_veilstone_store", items.items["bag"].label])
        if "beauty" in mthd:
            reqd_items.extend(["event_veilstone_city", items.items["poffin_case"].label, "event_hearthome_city", items.items["bag"].label])

        return HasAll(*reqd_items)

    def get_mon_rule(self, mon: str) -> Rule:
        return Has(f"mon_{mon}")

    def get_once_mon_rule(self, mon: str) -> Rule:
        return Has(f"once_mon_{mon}")

    def get_roamer_rule(self, roamer: int) -> Rule:
        return Has(f"event_roamer_{roamer}")
