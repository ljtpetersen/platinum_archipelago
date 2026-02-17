# species.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Tuple

from BaseClasses import Region

from worlds.pokemon_platinum.locations import PokemonPlatinumLocation
from worlds.pokemon_platinum.options import UnownsOption
from worlds.pokemon_platinum.regions import is_region_enabled

from .data import special_encounters, map_header_labels
from .data.encounters import encounters as encounterdata, encounter_type_pairs, EncounterSlot, national_dex_requiring_encs
from .data.regions import regions as regiondata
from .data.species import species as speciesdata, regional_mons
from .data.trainers import trainers as trainerdata, trainer_party_supporting_starters, trainer_requires_national_dex

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

def make_evolution_map() -> Mapping[str, Sequence[str]]:
    ret = {}
    for name, spec in speciesdata.items():
        if spec.pre_evolution:
            from_spec = spec.pre_evolution.species 
            if from_spec not in ret:
                ret[from_spec] = [name]
            else:
                ret[from_spec].append(name)
    return ret

evolutions: Mapping[str, Sequence[str]] = make_evolution_map()

def get_species_set() -> Set[str]:
    return set(speciesdata)

def get_two_level_evo_species() -> Set[str]:
    def has_two_level_evo(spec: str) -> bool:
        for _ in range(2):
            for evo_to in evolutions.get(spec, []):
                pevo = speciesdata[evo_to].pre_evolution
                if pevo.method == "level": # type: ignore
                    spec = evo_to
                    continue
            else:
                return False
        else:
            return True
    return {spec for spec in speciesdata if has_two_level_evo(spec)}

def randomize_starters(world: "PokemonPlatinumWorld") -> None:
    if not world.options.randomize_starters:
        world.generated_starters = ("turtwig", "chimchar", "piplup")
    elif len(world.options.starter_whitelist.value) > 0:
        selection = sorted(world.options.starter_whitelist.value)
        world.generated_starters = tuple(world.random.sample(selection, k=3)) # type: ignore
    else:
        if world.options.require_two_level_evolution_starters:
            selection_set = get_two_level_evo_species()
        else:
            selection_set = get_species_set()
        selection_set -= world.options.starter_blacklist.blacklist()
        world.generated_starters = tuple(world.random.sample(sorted(selection_set), k=3)) # type: ignore
    if world.options.randomize_intro_mon:
        world.generated_buneary = world.random.choice(sorted(get_species_set()))
    else:
        world.generated_buneary = "buneary"

def fill_unrandomized_encounters(world: "PokemonPlatinumWorld") -> Set[str]:
    done_map_headers = set()
    accessible_mons = set()
    acc_suc = set() if world.options.start_with_swarms else {"swarms"}
    for name, rd in regiondata.items():
        if not is_region_enabled(name, world.options):
            continue
        if rd.header in done_map_headers:
            continue
        done_map_headers.add(rd.header)
        if rd.header not in encounterdata:
            continue
        encs = encounterdata[rd.header]
        for type, table in encounter_type_pairs:
            if type == "water" and table not in world.options.in_logic_encounters:
                continue
            tbl: Sequence[EncounterSlot] = getattr(encs, table)
            for i, slot in enumerate(tbl):
                if slot.accessibility and not (set(slot.accessibility) & world.options.in_logic_encounters.value):
                    continue
                world.generated_encounters[(rd.header, table, i)] = slot.species
                if world.options.pokedex or (rd.header not in national_dex_requiring_encs and (not slot.accessibility or (set(slot.accessibility) - acc_suc) & world.options.in_logic_encounters.value)):
                    accessible_mons.add(slot.species)

    for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]:
        if nm in world.options.in_logic_encounters:
            for i, spec in enumerate(getattr(special_encounters, nm)):
                world.generated_speencs[(nm, i)] = spec
                if world.options.pokedex or nm not in special_encounters.requiring_national_dex:
                    accessible_mons.add(spec)

    return accessible_mons

def fill_unrandomized_trainer_parties(world: "PokemonPlatinumWorld") -> None:
    for name, rd in regiondata.items():
        if not is_region_enabled(name, world.options):
            continue
        for trainer in rd.trainers:
            for i, slot in enumerate(trainer_party_supporting_starters(trainer)):
                world.generated_trainer_parties[(trainer, i)] = slot.species

def randomize_encounters(world: "PokemonPlatinumWorld", req_specs: Set[str]) -> None:
    slots = {(rd.header, table, i)
        for name, rd in regiondata.items()
        if is_region_enabled(name, world.options) and rd.header in encounterdata \
            and (world.options.unown_option != UnownsOption.option_vanilla or not rd.header.startswith("solaceon_ruins"))
        for type, table in encounter_type_pairs
        if type != "water" or table in world.options.in_logic_encounters
        for i, slot in enumerate(getattr(encounterdata[rd.header], table))
        if not slot.accessibility or set(slot.accessibility) & world.options.in_logic_encounters.value
    }
    # roamers are not included here.
    speenc_slots = {(nm, i)
        for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
        if nm in world.options.in_logic_encounters
        for i in range(len(getattr(special_encounters, nm)))
    }
    if world.options.pokedex:
        before_dex_slots = sorted(slots)
        before_dex_slots_spe = sorted(speenc_slots)
        after_dex_slots = []
        after_dex_slots_spe = []
    else:
        acc_suc = set() if world.options.start_with_swarms else {"swarms"}
        before_dex_slots_set = {(rd.header, table, i)
            for name, rd in regiondata.items()
            if is_region_enabled(name, world.options) and rd.header in encounterdata \
                and (world.options.unown_option != UnownsOption.option_vanilla or not rd.header.startswith("solaceon_ruins")) \
                and rd.header not in national_dex_requiring_encs
            for type, table in encounter_type_pairs
            if type != "water" or table in world.options.in_logic_encounters
            for i, slot in enumerate(getattr(encounterdata[rd.header], table))
            if not slot.accessibility or (set(slot.accessibility) - acc_suc) & world.options.in_logic_encounters.value
        }
        before_dex_slots_spe_set = {(nm, i)
            for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
            if nm in world.options.in_logic_encounters and nm not in special_encounters.requiring_national_dex
            for i in range(len(getattr(special_encounters, nm)))
        }
        before_dex_slots = sorted(before_dex_slots_set)
        before_dex_slots_spe = sorted(before_dex_slots_spe_set)
        after_dex_slots = sorted(slots - before_dex_slots_set)
        after_dex_slots_spe = sorted(speenc_slots - before_dex_slots_spe_set)
    min_unique_count = world.options.dexsanity_count
    assert min_unique_count <= len(slots) + len(speenc_slots)
    before_mons = sorted(req_specs)
    assert len(before_mons) <= len(before_dex_slots) + len(before_dex_slots_spe)
    bl = world.options.encounter_species_blacklist.blacklist()
    new_specs = []
    if len(before_mons) < min_unique_count:
        pokemon_pool = [mon for mon in speciesdata if mon not in req_specs and mon not in bl]
        new_specs.extend(world.random.sample(pokemon_pool, k=min_unique_count - len(req_specs)))
    pokemon_pool = [mon for mon in speciesdata if mon not in bl]
    new_specs += world.random.choices(pokemon_pool, k=len(slots) + len(speenc_slots) - len(new_specs) - len(before_mons))
    world.random.shuffle(new_specs)
    centre = len(before_dex_slots) + len(before_dex_slots_spe) - len(before_mons)
    before_mons.extend(new_specs[:centre])
    after_mons = new_specs[centre:]
    world.random.shuffle(before_mons)
    world.random.shuffle(after_mons)
    world.generated_encounters.update({slot:spec for slot, spec in zip(before_dex_slots, before_mons)})
    world.generated_speencs.update({slot:spec for slot, spec in zip(before_dex_slots_spe, before_mons[len(before_dex_slots):])})
    world.generated_encounters.update({slot:spec for slot, spec in zip(after_dex_slots, after_mons)})
    world.generated_speencs.update({slot:spec for slot, spec in zip(after_dex_slots_spe, after_mons[len(after_dex_slots):])})

    if world.options.unown_option == UnownsOption.option_vanilla:
        sol_ruins_slots = sorted({(rd.header, table, i)
            for name, rd in regiondata.items()
            if is_region_enabled(name, world.options) and rd.header in encounterdata \
                and rd.header.startswith("solaceon_ruins")
            for type, table in encounter_type_pairs
            if type != "water" or table in world.options.in_logic_encounters
            for i, slot in enumerate(getattr(encounterdata[rd.header], table))
            if not slot.accessibility or set(slot.accessibility) & world.options.in_logic_encounters.value
        })
        world.generated_encounters.update({slot:"unown" for slot in sol_ruins_slots})

def randomize_trainer_parties(world: "PokemonPlatinumWorld", req_specs: Set[str]) -> None:
    slots = {(trainer, i)
        for name, rd in regiondata.items()
        if is_region_enabled(name, world.options)
        for trainer in rd.trainers
        for i in range(len(trainer_party_supporting_starters(trainer)))
    }
    if world.options.pokedex:
        before_slots = sorted(slots)
        after_slots = []
    else:
        before_slots_set = {(trainer, i)
            for name, rd in regiondata.items()
            if is_region_enabled(name, world.options)
            for trainer in rd.trainers
            if not trainer_requires_national_dex(trainer)
            for i in range(len(trainer_party_supporting_starters(trainer)))
        }
        before_slots = sorted(before_slots_set)
        after_slots = sorted(slots - before_slots_set)
    before_mons = sorted(req_specs)
    assert len(before_mons) <= len(before_slots)
    bl = world.options.trainer_party_blacklist.blacklist()
    pokemon_pool = [mon for mon in speciesdata if mon not in bl]
    new_specs = world.random.choices(pokemon_pool, k=len(slots) - len(before_mons))
    centre = len(before_slots) - len(before_mons)
    before_mons.extend(new_specs[:centre])
    after_mons = new_specs[centre:]
    world.random.shuffle(before_mons)
    world.random.shuffle(after_mons)
    world.generated_trainer_parties.update({slot:spec for slot, spec in zip(before_slots, before_mons)})
    world.generated_trainer_parties.update({slot:spec for slot, spec in zip(after_slots, after_mons)})


def randomize_trainer_parties_and_encounters(world: "PokemonPlatinumWorld") -> None:
    if world.options.randomize_encounters and world.options.randomize_trainer_parties:
        bl = world.options.encounter_species_blacklist.blacklist()
        rm_set = set(regional_mons)
        all_enc = rm_set - bl
        bl = world.options.trainer_party_blacklist.blacklist()
        all_trp = rm_set - bl
        just_enc = all_enc - all_trp
        just_trp = all_trp - all_enc
        both = all_enc & all_trp
        req_regionals = max(50, world.options.regional_dex_goal.value)
        centre = world.random.randint(0, len(both))
        both_seq = sorted(both)
        world.random.shuffle(both_seq)
        poss_enc = sorted(just_enc) + both_seq[:centre]
        poss_trp = sorted(just_trp) + both_seq[centre:]
        num_enc = world.random.randint(max(0, req_regionals - len(poss_trp)), min(len(poss_enc), req_regionals))
        num_trp = req_regionals - num_enc
        amity_square_mon = world.random.choice([
            "pikachu",
            "clefairy",
            "jigglypuff",
            "psyduck",
            "torchic",
            "shroomish",
            "skitty",
            "turtwig",
            "grotle",
            "torterra",
            "chimchar",
            "monferno",
            "infernape",
            "piplup",
            "prinplup",
            "empoleon",
            "pachirisu",
            "drifloon",
            "buneary",
            "happiny",
        ])
        randomize_encounters(world, set(world.random.sample(poss_enc, k=num_enc)) | {"munchlax", "kecleon", "geodude", amity_square_mon})
        randomize_trainer_parties(world, set(world.random.sample(poss_trp, k=num_trp)))
    elif world.options.randomize_encounters:
        bl = world.options.encounter_species_blacklist.blacklist()
        regional_mons_set = set(regional_mons)
        if world.options.pokedex:
            regional_party_mons = {ps.species
                for region_name, region in regiondata.items()
                if is_region_enabled(region_name, world.options)
                for trainer in region.trainers
                for ps in trainer_party_supporting_starters(trainer)
                if ps.species in regional_mons_set}
        else:
            regional_party_mons = {ps.species
                for region_name, region in regiondata.items()
                if is_region_enabled(region_name, world.options)
                for trainer in region.trainers
                if not trainer_requires_national_dex(trainer)
                for ps in trainer_party_supporting_starters(trainer)
                if ps.species in regional_mons_set}
        regional_mons_set -= bl
        df = max(50, world.options.regional_dex_goal.value) - len(regional_party_mons)
        if 0 >= df:
            req_encounter_specs = set()
        else:
            req_encounter_specs = set(world.random.sample(sorted(regional_mons_set - regional_party_mons), k=df))
        amity_square_mon = world.random.choice([
            "pikachu",
            "clefairy",
            "jigglypuff",
            "psyduck",
            "torchic",
            "shroomish",
            "skitty",
            "turtwig",
            "grotle",
            "torterra",
            "chimchar",
            "monferno",
            "infernape",
            "piplup",
            "prinplup",
            "empoleon",
            "pachirisu",
            "drifloon",
            "buneary",
            "happiny",
        ])
        randomize_encounters(world, req_encounter_specs | {"munchlax", "kecleon", "geodude", amity_square_mon})
        fill_unrandomized_trainer_parties(world)
    elif world.options.randomize_trainer_parties:
        bl = world.options.trainer_party_blacklist.blacklist()
        regional_mons_set = set(regional_mons)
        regional_encounter_mons = fill_unrandomized_encounters(world) & regional_mons_set
        regional_mons_set -= bl
        df = max(50, world.options.regional_dex_goal) - len(regional_encounter_mons)
        if 0 >= df:
            req_part_specs = set()
        else:
            req_part_specs = set(world.random.sample(sorted(regional_mons_set - regional_encounter_mons), k=df))
        randomize_trainer_parties(world, req_part_specs)
    else:
        fill_unrandomized_encounters(world)
        fill_unrandomized_trainer_parties(world)

def randomize_roamers(world: "PokemonPlatinumWorld") -> None:
    if world.options.randomize_roamers:
        bl = world.options.roamer_blacklist.blacklist()
        pokemon_pool = [mon for mon in speciesdata if mon not in bl]
        world.generated_roamers = tuple(world.random.sample(pokemon_pool, k=5)) # type: ignore
    else:
        world.generated_roamers = tuple(special_encounters.roamers[i] for i in [0, 1, 3, 4, 5]) # type: ignore

def fill_species(world: "PokemonPlatinumWorld") -> None:
    for (trainer, i), spec in world.generated_trainer_parties.items():
        world.multiworld.get_location(f"{trainer}_party_{i + 1}", world.player).place_locked_item(world.create_event(f"see_mon_{spec}"))
    for (hdr, tbl, i), spec in world.generated_encounters.items():
        world.multiworld.get_location(f"{hdr}_{tbl}_{i + 1}", world.player).place_locked_item(world.create_event(f"mon_{spec}"))
    for (speenc, i), spec in world.generated_speencs.items():
        if speenc.endswith("honey_tree"):
            if speenc == "regular_honey_tree":
                world.multiworld.get_location(f"speenc_regular_honey_tree_{i + 1}", world.player).place_locked_item(world.create_event(f"mon_{spec}"))
                world.multiworld.get_location(f"speenc_munchlax_honey_tree_{i + 1}", world.player).place_locked_item(world.create_event(f"mon_{spec}"))
            else:
                world.multiworld.get_location(f"speenc_munchlax_honey_tree_{len(special_encounters.regular_honey_tree) + i + 1}", world.player).place_locked_item(world.create_event(f"mon_{spec}"))
        else:
            world.multiworld.get_location(f"speenc_{speenc}_{i + 1}", world.player).place_locked_item(world.create_event(f"mon_{spec}"))

    if "roamers" in world.options.in_logic_encounters:
        for i, spec in zip([0, 1, 3, 4, 5], world.generated_roamers):
            world.multiworld.get_location(f"roamer_{i}", world.player).place_locked_item(world.create_event(f"once_mon_{spec}"))

def add_virt_specs(world: "PokemonPlatinumWorld", regions: Mapping[str, Region]) -> None:
    accessible_mons = set(world.generated_encounters.values()) | set(world.generated_speencs.values())
    while True:
        to_add = set()
        for mon, data in speciesdata.items():
            if mon in accessible_mons or data.pre_evolution is None:
                continue
            if data.pre_evolution.species not in accessible_mons:
                continue
            if data.pre_evolution.method not in world.options.in_logic_evolution_methods:
                continue
            if data.pre_evolution.other_species is not None and data.pre_evolution.other_species not in accessible_mons:
                continue
            to_add.add(mon)
        accessible_mons |= to_add
        if not to_add:
            break
    accessible_once_mons = accessible_mons.copy()
    if "roamers" in world.options.in_logic_encounters:
        accessible_once_mons |= set(world.generated_roamers)
    accessible_see_mons = accessible_once_mons | set(world.generated_trainer_parties.values())

    am_set = accessible_mons
    accessible_mons = sorted(accessible_mons)
    world.accessible_mons = accessible_mons
    accessible_once_mons = sorted(accessible_once_mons)
    world.accessible_once_mons = accessible_once_mons
    accessible_see_mons = sorted(accessible_see_mons)
    world.accessible_see_mons = accessible_see_mons

    reg = regions["virt_specs"]
    for mon in accessible_mons:
        location = PokemonPlatinumLocation(
            world.player,
            f"mon_map_{mon}",
            "once_mon_event",
            parent=reg,
        )
        location.show_in_spoiler = False
        location.place_locked_item(world.create_event(f"once_mon_{mon}"))
        reg.locations.append(location)
        data = speciesdata[mon]
        if data.pre_evolution is None \
            or data.pre_evolution.species not in am_set \
            or data.pre_evolution.method not in world.options.in_logic_evolution_methods \
            or data.pre_evolution.other_species is not None and data.pre_evolution.other_species not in am_set:
            continue
        location = PokemonPlatinumLocation(
            world.player,
            f"evo_to_{mon}",
            "mon_event",
            parent=reg
        )
        location.show_in_spoiler = False
        location.place_locked_item(world.create_event(f"mon_{mon}"))
        reg.locations.append(location)

    for mon in accessible_once_mons:
        location = PokemonPlatinumLocation(
            world.player,
            f"mon_map_once_{mon}",
            "see_mon_event",
            parent=reg,
        )
        location.show_in_spoiler = False
        location.place_locked_item(world.create_event(f"see_mon_{mon}"))
        reg.locations.append(location)

    world.dexsanity_specs = world.random.sample(accessible_once_mons, k=world.options.dexsanity_count.value)

def encounter_slot_label(key: Tuple[str, str, int], in_logic_encounters: Set[str]) -> str:
    (header, table, index) = key
    def nicer_str(s):
        return " ".join(v[:1].upper() + v[1:] for v in s.split("_"))

    map_label = map_header_labels[header]
    map_label += f" ({nicer_str(table)})"
    slot: EncounterSlot = getattr(encounterdata[header], table)[index]
    if slot.accessibility:
        map_label += " (by any of {{{}}})".format(', '.join(nicer_str(v) for v in sorted(set(slot.accessibility) & in_logic_encounters)))
    return map_label

speenc_labels: Mapping[str, str] = {
    "regular_honey_tree": "Honey Tree (Normal)",
    "munchlax_honey_tree": "Honey Tree (Munchlax)",
    "trophy_garden": "Trophy Garden",
    "great_marsh_observatory": "Great Marsh Observatory",
    "great_marsh_observatory_national_dex": "Great Marsh Observatory (With National Dex)",
    "feebas_fishing": "Feebas Fishing",
    "odd_keystone": "Odd Keystone",
}

roamer_labels: Sequence[str] = [
    "Roamer (Interact with Mesprit)",
    "Roamer (Interact with Cresselia)",
    "Roamer (Talk with Oak in Eterna)",
    "Roamer (Talk with Oak in Eterna)",
    "Roamer (Talk with Oak in Eterna)",
]
