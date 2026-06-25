# rules.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .data import encounters as encounterdata, Hm, regions as regiondata, rules as ruledata, trainers as trainerdata, species as speciesdata
from .locations import is_location_in_world, get_parent_region
from .options import Goal, HMReaderMode, TMHMCompatibility
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
            rule = ruledata.create_hm_badge_rule(hm)
        else:
            rule = ruledata.True_()
        common_rules[f"{hm.name.lower()}_badge"] = rule
    rules = ruledata.Rules(common_rules, world.options)

    rules.fill_rules()

    world.ruledata = rules

    for (src, dest), rule in rules.exit_rules.items():
        if is_region_enabled(src, world.options) and is_region_enabled(dest, world.options):
            world.set_rule(world.multiworld.get_entrance(f"{src} -> {dest}", world.player), rule)

    for loc in world.multiworld.get_locations(world.player):
        if loc.type in rules.location_type_rules and loc.name in rules.location_rules: # type: ignore
            world.set_rule(loc, rules.location_type_rules[loc.type] & rules.location_rules[loc.name]) # type: ignore
        elif loc.type in rules.location_type_rules: # type: ignore
            world.set_rule(loc, rules.location_type_rules[loc.type]) # type: ignore
        elif loc.name in rules.location_rules:
            world.set_rule(loc, rules.location_rules[loc.name])

    for name, rule in rules.trainer_rules.items():
        if name.startswith("rival_"):
            parent_region = trainerdata.trainers[name + "_turtwig"].parent_region
        else:
            parent_region = trainerdata.trainers[name].parent_region
        if is_region_enabled(parent_region, world.options):
            world.set_rule(world.multiworld.get_entrance(f"{parent_region} -> trainer_{name}", world.player), rule)

    done_headers = set()
    for region_name, region_data in regiondata.regions.items():
        header = region_data.header
        if not is_region_enabled(region_name, world.options):
            continue
        for type in region_data.accessible_encounters:
            if header in encounterdata.encounters and (header, type) not in done_headers:
                done_headers.add((header, type))
                for table in encounterdata.encounter_type_tables[type]:
                    e: Sequence[encounterdata.EncounterSlot] = getattr(encounterdata.encounters[header], table)
                    if not e:
                        continue
                    if type == "water" and table in (rules.encounter_type_rules.keys() & world.options.in_logic_encounters):
                        for i in range(len(e)):
                            world.set_rule(world.multiworld.get_location(f"{header}_{table}_{i + 1}", world.player), rules.encounter_type_rules[table])
                    elif type == "land":
                        for i, slot in enumerate(e):
                            if slot.accessibility and (set(slot.accessibility) & world.options.in_logic_encounters.value):
                                world.set_rule(world.multiworld.get_location(f"{header}_land_{i + 1}", world.player), rules.get_enc_accessibility_rule(slot.accessibility))
                    elif type == "long_grass":
                        accessibility_mask = (encounterdata.possible_accessibilities - {"radar"}) & world.options.in_logic_encounters.value
                        for i, slot in enumerate(e):
                            if slot.accessibility and (set(slot.accessibility) & accessibility_mask):
                                world.set_rule(world.multiworld.get_location(f"{header}_long_grass_land_{i + 1}", world.player), rules.get_enc_accessibility_rule(slot.accessibility))
        if region_data.honey_tree_idx is not None:
            world.set_rule(world.multiworld.get_entrance(f"{region_name} -> speenc_regular_honey_tree", world.player), rules.encounter_type_rules["regular_honey_tree"])
            if region_data.honey_tree_idx in world.generated_munchlax_trees:
                world.set_rule(world.multiworld.get_entrance(f"{region_name} -> speenc_munchlax_honey_tree", world.player), rules.encounter_type_rules["munchlax_honey_tree"])

    for mon in world.dexsanity_specs:
        world.set_rule(world.multiworld.get_location(f"Pokedex - " + speciesdata.species[mon].label, world.player), rules.get_once_mon_rule(mon))

    am_set = frozenset(world.accessible_mons)
    for mon in world.accessible_mons:
        world.set_rule(world.multiworld.get_location(f"mon_map_{mon}", world.player), rules.get_mon_rule(mon))
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
            world.set_rule(world.multiworld.get_location(f"evo_to_{mon}", world.player), rule)
    for mon in world.accessible_once_mons:
        world.set_rule(world.multiworld.get_location(f"mon_map_once_{mon}", world.player), rules.get_once_mon_rule(mon))

    if "roamers" in world.options.in_logic_encounters:
        for i in [0, 1, 3, 4, 5]:
            world.set_rule(world.multiworld.get_location(f"roamer_{i}", world.player), rules.get_roamer_rule(i))

    match world.options.goal.value:
        case Goal.option_champion:
            goal_event = "event_beat_cynthia"
        case _:
            raise ValueError(f"invalid goal {world.options.goal}")
    world.set_completion_rule(ruledata.Has(goal_event))

def verify_hm_accessibility(world: "PokemonPlatinumWorld") -> None:
    if world.options.hm_reader_mode == HMReaderMode.option_noreq_mon or world.options.tmhm_compatibility != TMHMCompatibility.option_none:
        return
    rules = world.ruledata

    def do_verify(hms: list[Hm]):

        rsvds = {
            hm:rules.common_rules["use_" + hm.name.lower()]._instantiate(world)
            for hm in Hm
        }
        while True:
            hms_to_verify = hms.copy()
            unverified_hms = []
            last_hm = None

            while hms_to_verify:
                state = world.get_world_collection_state()
                hm_to_verify = hms_to_verify[-1]
                if not rsvds[hm_to_verify]._evaluate(state):
                    if last_hm == hm_to_verify:
                        if not rsvds[hm_to_verify]._evaluate(state):
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
                else:
                    hms_to_verify.pop()
            if unverified_hms and unverified_hms == hms:
                state = world.get_world_collection_state()
                if any(rsvds[hm]._evaluate(state) for hm in unverified_hms):
                    raise Exception(f"Failed to ensure access to {'\n'.join(unverified_hms)} for player {world.player}")
            elif unverified_hms:
                unverified_hms.reverse()
            else:
                break
    hms = [hm for hm in Hm]
    world.random.shuffle(hms)
    do_verify(hms)
