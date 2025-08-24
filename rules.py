# rules.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import CollectionState
from typing import TYPE_CHECKING
from worlds.generic.Rules import set_rule

from .data import Hm, items as itemdata, locations as locationdata, rules as ruledata
from .locations import location_types, raw_id_to_const_name

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

def always_true(_: CollectionState) -> bool:
    return True

def is_location_present(label: str, world: "PokemonPlatinumWorld") -> bool:
    if label.startswith("event_"):
        return True
    const_name = raw_id_to_const_name[world.location_name_to_id[label]]
    return location_types[locationdata.locations[const_name].type].is_enabled(world.options) or const_name in locationdata.required_locations

def set_rules(world: "PokemonPlatinumWorld") -> None:
    common_rules = {}
    for hm in Hm:
        if world.options.requires_badge(hm.name):
            rule = ruledata.create_hm_badge_rule(hm, world.player)
        else:
            rule = always_true
        common_rules[f"{hm.name.lower()}_badge"] = rule
    rules = ruledata.Rules(world.player, common_rules)
    if world.options.visibility_hm_logic.value == 1:
        common_rules["flash_if_opt"] = common_rules["flash"]
        common_rules["defog_if_opt"] = common_rules["defog"]
    else:
        common_rules["flash_if_opt"] = always_true
        common_rules["defog_if_opt"] = always_true
    if world.options.dowsing_machine_logic.value == 1:
        common_rules["dowsingmachine_if_opt"] = lambda state : state.has_all([
            itemdata.items["dowsingmachine"].label,
            itemdata.items["poketch"].label,
        ], world.player)
    else:
        common_rules["dowsingmachine_if_opt"] = always_true

    rules.fill_rules()

    for name, rule in rules.exit_rules.items():
        set_rule(world.multiworld.get_entrance(name, world.player), rule)

    for name, rule in rules.location_rules.items():
        if is_location_present(name, world):
            set_rule(world.multiworld.get_location(name, world.player), rule)

    match world.options.goal.value:
        case 0:
            goal_event = "event_beat_cynthia"
        case _:
            raise ValueError(f"invalid goal {world.options.goal}")
    world.multiworld.completion_condition[world.player] = lambda state : state.has(goal_event, world.player)

