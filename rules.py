# rules.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import CollectionState
from typing import TYPE_CHECKING
from worlds.generic.Rules import set_rule

from .data import Hm, items as itemdata, rules as ruledata
from .locations import is_location_enabled, get_parent_region
from .regions import is_event_region_enabled, is_region_enabled

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

def always_true(_: CollectionState) -> bool:
    return True

def is_location_present(label: str, world: "PokemonPlatinumWorld") -> bool:
    if label.startswith("event_") and is_event_region_enabled(label, world.options):
        return True
    parent_region = get_parent_region(label, world)
    return is_region_enabled(parent_region, world.options) and is_location_enabled(label, world)

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

    for (src, dest), rule in rules.exit_rules.items():
        if is_region_enabled(src, world.options) and is_region_enabled(dest, world.options):
            set_rule(world.multiworld.get_entrance(f"{src} -> {dest}", world.player), rule)

    for name, rule in rules.location_rules.items():
        if is_location_present(name, world):
            set_rule(world.multiworld.get_location(name, world.player), rule)

    match world.options.goal.value:
        case 0:
            goal_event = "event_beat_cynthia"
        case _:
            raise ValueError(f"invalid goal {world.options.goal}")
    world.multiworld.completion_condition[world.player] = lambda state : state.has(goal_event, world.player)

