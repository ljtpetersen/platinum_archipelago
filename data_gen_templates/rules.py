
from BaseClasses import CollectionState
from collections.abc import Callable, Mapping, MutableMapping
from . import Hm
from .species import species

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
    common_rules: MutableMapping[str, Rule]
    
    def __init__(self, player: int, common_rules: MutableMapping[str, Rule]):
        self.player = player
        self.common_rules = common_rules
        self.common_rules.update({ hm.name.lower():self.create_hm_rule(hm, player) for hm in Hm })

    def fill_rules(self):
        self.exit_rules = {
            # TEMPLATE: EXIT_RULES
        }
        self.location_rules = {
            # TEMPLATE: LOCATION_RULES
        }

    def create_hm_rule(self, hm: Hm, player: int) -> Rule:
        mons = set()
        item_evols = []
        for name, spec in species.items():
            if hm not in spec.hms:
                continue
            mons.add(f"mon_{name}")
            while spec.pre_evolution:
                new_spec = species[spec.pre_evolution.species]
                if hm in new_spec.hms:
                    break
                if spec.pre_evolution.item:
                    item_evols.append([f"mon_{spec.pre_evolution.species}", spec.pre_evolution.item])
                else:
                    mons.add(f"mon_{spec.pre_evolution.species}")
                spec = new_spec

        def hm_rule(state: CollectionState) -> bool:
            if not (state.has(hm, player) and self.common_rules[f"{hm.name.lower()}_badge"]):
                return False
            if state.has_any(mons, player):
                return True
            for item_evol in item_evols:
                if state.has_all(item_evol, player):
                    return True
            return False

        return hm_rule
