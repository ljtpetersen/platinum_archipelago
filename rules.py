# rules.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Sequence
from BaseClasses import CollectionState
from typing import TYPE_CHECKING
from worlds.generic.Rules import add_rule, set_rule

from .data import encounters as encounterdata, Hm, items as itemdata, regions as regiondata, rules as ruledata, trainers as trainerdata, species as speciesdata
from .locations import is_location_in_world, get_parent_region
from .options import Goal, HMReaderMode
from .regions import is_event_region_enabled, is_region_enabled

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

def is_location_present(label: str, world: "PokemonPlatinumWorld") -> bool:
    if label.startswith("event_") and is_event_region_enabled(label, world.options):
        return True
    parent_region = get_parent_region(label, world)
    return is_region_enabled(parent_region, world.options) and is_location_in_world(label, world)

def set_rules(world: "PokemonPlatinumWorld") -> None:
    common_rules = {}
    for hm in Hm:
        if world.options.requires_badge(hm.name):
            rule = ruledata.create_hm_badge_rule(hm, world.player)
        else:
            rule = ruledata.always_true
        common_rules[f"{hm.name.lower()}_badge"] = rule
    rules = ruledata.Rules(world.player, common_rules, world.options)

    rules.fill_rules()

    world.ruledata = rules

    for (src, dest), rule in rules.exit_rules.items():
        if is_region_enabled(src, world.options) and is_region_enabled(dest, world.options):
            set_rule(world.multiworld.get_entrance(f"{src} -> {dest}", world.player), rule)

    for name, rule in rules.location_rules.items():
        if is_location_present(name, world):
            set_rule(world.multiworld.get_location(name, world.player), rule)

    for loc in world.multiworld.get_locations(world.player):
        if loc.type in rules.location_type_rules: # type: ignore
            add_rule(loc, rules.location_type_rules[loc.type]) # type: ignore

    for name, rule in rules.trainer_rules.items():
        if name.startswith("rival_"):
            parent_region = trainerdata.trainers[name + "_turtwig"].parent_region
        else:
            parent_region = trainerdata.trainers[name].parent_region
        if is_region_enabled(parent_region, world.options):
            set_rule(world.multiworld.get_entrance(f"{parent_region} -> trainer_{name}", world.player), rule)

    done_headers = set()
    for region_name, region_data in regiondata.regions.items():
        header = region_data.header
        if not is_region_enabled(region_name, world.options):
            continue
        if header in encounterdata.encounters and header not in done_headers:
            done_headers.add(header)
            for type, table in encounterdata.encounter_type_pairs:
                e: Sequence[encounterdata.EncounterSlot] = getattr(encounterdata.encounters[header], table)
                if not e:
                    continue
                if type == "water" and table in (rules.encounter_type_rules.keys() & world.options.in_logic_encounters):
                    for i in range(len(e)):
                        set_rule(world.multiworld.get_location(f"{header}_{table}_{i + 1}", world.player), rules.encounter_type_rules[table])
                elif type == "land":
                    for i, slot in enumerate(e):
                        if slot.accessibility and (set(slot.accessibility) & world.options.in_logic_encounters.value):
                            set_rule(world.multiworld.get_location(f"{header}_land_{i + 1}", world.player), rules.get_enc_accessibility_rule(slot.accessibility))
        if region_data.honey_tree_idx is not None:
            set_rule(world.multiworld.get_entrance(f"{region_name} -> speenc_regular_honey_tree", world.player), rules.encounter_type_rules["regular_honey_tree"])
            if region_data.honey_tree_idx in world.generated_munchlax_trees:
                set_rule(world.multiworld.get_entrance(f"{region_name} -> speenc_munchlax_honey_tree", world.player), rules.encounter_type_rules["munchlax_honey_tree"])

    for mon in world.dexsanity_specs:
        set_rule(world.multiworld.get_location(f"Dexsanity - " + speciesdata.species[mon].label, world.player), rules.get_once_mon_rule(mon))

    am_set = frozenset(world.accessible_mons)
    for mon in world.accessible_mons:
        set_rule(world.multiworld.get_location(f"mon_map_{mon}", world.player), rules.get_mon_rule(mon))
        data = speciesdata.species[mon]
        if data.pre_evolution is None:
            continue
        pevo = data.pre_evolution
        if pevo.species not in am_set \
            or pevo.method not in world.options.in_logic_evolution_methods \
            or pevo.other_species is not None and pevo.other_species not in am_set:
            continue
        rule = rules.get_pevo_rule(pevo, world.options)
        if rule is not None:
            set_rule(world.multiworld.get_location(f"evo_to_{mon}", world.player), rule)
    for mon in world.accessible_once_mons:
        set_rule(world.multiworld.get_location(f"mon_map_once_{mon}", world.player), rules.get_once_mon_rule(mon))

    if "roamers" in world.options.in_logic_encounters:
        for i in [0, 1, 3, 4, 5]:
            set_rule(world.multiworld.get_location(f"roamer_{i}", world.player), rules.get_roamer_rule(i))

    match world.options.goal.value:
        case Goal.option_champion:
            goal_event = "event_beat_cynthia"
        case _:
            raise ValueError(f"invalid goal {world.options.goal}")
    world.multiworld.completion_condition[world.player] = lambda state : state.has(goal_event, world.player)

def verify_hm_accessibility(world: "PokemonPlatinumWorld") -> None:
    if world.options.hm_reader_mode == HMReaderMode.option_noreq_mon:
        return
    rules = world.ruledata

    def do_verify(hms: list[Hm]):
        while True:
            hms_to_verify = hms.copy()
            unverified_hms = []
            last_hm = None

            while hms_to_verify:
                state = world.get_world_collection_state()
                hm_to_verify = hms_to_verify[-1]
                if not rules.common_rules["use_" + hm_to_verify.name.lower()](state):
                    if last_hm == hm_to_verify:
                        if not rules.common_rules["use_" + hm_to_verify.name.lower()](state):
                            unverified_hms.append(hms_to_verify.pop())
                        else:
                            hms_to_verify.pop()
                        continue
                    last_hm = hm_to_verify
                    valid_pokemon = [mon for mon in world.accessible_mons if state.has(f"mon_{mon}", world.player)]
                    pokemon = world.random.choice(valid_pokemon)
                    rules.hm_mons[hm_to_verify].append("mon_" + pokemon)
                    world.added_hm_compatibility.setdefault(pokemon, []).append(hm_to_verify)
                    print("added compat:", pokemon, hm_to_verify)
                    print(rules.common_rules["use_" + hm_to_verify.name.lower()](state))
                else:
                    hms_to_verify.pop()
            if unverified_hms and unverified_hms == hms:
                state = world.get_world_collection_state()
                if any(world.common_rules[hm.name.lower() + "_badge"](state) for hm in unverified_hms):
                    raise Exception(f"Failed to ensure access to {'\n'.join(unverified_hms)} for player {world.player}")
            elif unverified_hms:
                unverified_hms.reverse()
            else:
                break
    hms = [hm for hm in Hm]
    world.random.shuffle(hms)
    do_verify(hms)
