# regions.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import Region
from collections.abc import Callable, Mapping, MutableSet, Sequence
from dataclasses import dataclass
from typing import Tuple, TYPE_CHECKING

from worlds.pokemon_platinum.options import PokemonPlatinumOptions

from .data import regions as regiondata
from .data.encounters import EncounterSlot, encounters, encounter_type_pairs, encounter_type_tables
from .data.trainers import trainer_party_supporting_starters
from .data import special_encounters
from .locations import PokemonPlatinumLocation

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

@dataclass(frozen=True)
class RegionType:
    is_enabled: Callable[[PokemonPlatinumOptions], bool]

region_groups: Mapping[str, RegionType] = {
    "generic": RegionType(is_enabled = lambda _ : True),
    "fight_area": RegionType(is_enabled = lambda _ : True),
}

def is_region_enabled(region: str | None, opts: PokemonPlatinumOptions) -> bool:
    if region is not None:
        if region in regiondata.regions:
            return region_groups[regiondata.regions[region].group].is_enabled(opts)
        else:
            return True
    else:
        return False

def is_event_region_enabled(event: str, opts: PokemonPlatinumOptions) -> bool:
    return is_region_enabled(regiondata.event_region_map[event], opts)

def create_regions(world: "PokemonPlatinumWorld") -> Mapping[str, Region]:
    regions: Mapping[str, Region] = {}
    connections: Sequence[Tuple[str, str, str]] = []

    def setup_wild_regions(parent_region: Region, wild_region_data: regiondata.RegionData) -> None:
        header = wild_region_data.header
        if header not in encounters:
            return
        encs = encounters[wild_region_data.header]
        for type in wild_region_data.accessible_encounters:
            name = f"{header}_{type}"
            if name not in regions:
                wild_region = Region(name, world.player, world.multiworld)
                regions[name] = wild_region
                for table in encounter_type_tables[type]:
                    if type == "water" and table not in world.options.in_logic_encounters:
                        continue
                    e: Sequence[EncounterSlot] = getattr(encs, table)
                    if not e:
                        continue

                    for i, slot in enumerate(e):
                        if slot.accessibility and not set(slot.accessibility) & world.options.in_logic_encounters.value:
                            continue
                        location = PokemonPlatinumLocation(
                            world.player,
                            f"{header}_{table}_{i + 1}",
                            "mon_event",
                            parent=wild_region,
                        )
                        location.show_in_spoiler = False
                        wild_region.locations.append(location)
            else:
                wild_region = regions[name]
            parent_region.connect(wild_region, f"{parent_region.name} -> {name}")

    def setup_honey_tree(parent_region: Region, wild_region_data: regiondata.RegionData) -> None:
        if wild_region_data.honey_tree_idx is None:
            return
        name = "munchlax_honey_tree" if wild_region_data.honey_tree_idx in world.generated_munchlax_trees else "regular_honey_tree"
        if "speenc_" + name not in regions:
            wild_region = Region("speenc_" + name, world.player, world.multiworld)
            regions["speenc_" + name] = wild_region
            if "regular_honey_tree" in world.options.in_logic_encounters:
                for i in range(len(special_encounters.regular_honey_tree)):
                    location = PokemonPlatinumLocation(
                        world.player,
                        f"speenc_{name}_{i + 1}",
                        "mon_event",
                        parent=wild_region,
                    )
                    location.show_in_spoiler = False
                    wild_region.locations.append(location)
            if name == "munchlax_honey_tree" and "munchlax_honey_tree" in world.options.in_logic_encounters:
                for i in range(len(special_encounters.munchlax_honey_tree)):
                    location = PokemonPlatinumLocation(
                        world.player,
                        f"speenc_{name}_{i + len(special_encounters.regular_honey_tree) + 1}",
                        "mon_event",
                        parent=wild_region,
                    )
                    location.show_in_spoiler = False
                    wild_region.locations.append(location)
        else:
            wild_region = regions["speenc_" + name]
        parent_region.connect(wild_region, f"{parent_region.name} -> speenc_{name}")

    def setup_special_encounters(parent_region: Region, wild_region_data: regiondata.RegionData) -> None:
        if wild_region_data.special_encounters is None or wild_region_data.special_encounters not in world.options.in_logic_encounters:
            return
        name = "speenc_" + wild_region_data.special_encounters
        if name not in regions:
            wild_region = Region(name, world.player, world.multiworld)
            regions[name] = wild_region
            for i in range(len(getattr(special_encounters, wild_region_data.special_encounters))):
                location = PokemonPlatinumLocation(
                    world.player,
                    f"{name}_{i + 1}",
                    "mon_event",
                    parent=wild_region,
                )
                location.show_in_spoiler = False
                wild_region.locations.append(location)
        else:
            wild_region = regions[name]
        parent_region.connect(wild_region, f"{parent_region.name} -> {name}")

    def setup_trainer_region(parent_region: Region, trainer: str) -> None:
        trainer_region = Region(f"trainer_{trainer}", world.player, world.multiworld)
        regions[f"trainer_{trainer}"] = trainer_region
        parent_region.connect(trainer_region, f"{parent_region.name} -> trainer_{trainer}")
        for i in range(len(trainer_party_supporting_starters(trainer))):
            location = PokemonPlatinumLocation(
                world.player,
                f"{trainer}_party_{i + 1}",
                "see_mon_event",
                parent=trainer_region
            )
            location.show_in_spoiler = False
            trainer_region.locations.append(location)


    ignored_regions: MutableSet[str] = set()
    for region_name, region_data in regiondata.regions.items():
        if not region_groups[region_data.group].is_enabled(world.options):
            ignored_regions.add(region_name)
            continue
        new_region = Region(region_name, world.player, world.multiworld)

        regions[region_name] = new_region

        for event in region_data.events:
            event_loc = PokemonPlatinumLocation(
                world.player,
                event,
                "event",
                parent=new_region)
            event_loc.show_in_spoiler = False
            event_loc.place_locked_item(world.create_event(event))
            new_region.locations.append(event_loc)

        setup_wild_regions(new_region, region_data)
        setup_honey_tree(new_region, region_data)
        setup_special_encounters(new_region, region_data)

        for trainer in region_data.trainers:
            setup_trainer_region(new_region, trainer)

        for region_exit in region_data.exits:
            connections.append((f"{region_name} -> {region_exit}", region_name, region_exit))

    for name, source, dest in connections:
        if dest in ignored_regions:
            continue
        regions[source].connect(regions[dest], name)

    if "roamers" in world.options.in_logic_encounters:
        roamreg = regions["virt_roamers"]
        for i in [0, 1, 3, 4, 5]:
            location = PokemonPlatinumLocation(
                world.player,
                f"roamer_{i}",
                "once_mon_event",
                parent=roamreg,
            )
            location.show_in_spoiler = False
            roamreg.locations.append(location)

    regions["Menu"] = Region("Menu", world.player, world.multiworld)
    regions["Menu"].connect(regions["twinleaf_town_player_house_2f"], "Start Game")

    return regions
