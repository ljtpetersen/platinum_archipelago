from BaseClasses import Region
from collections.abc import Mapping, Sequence
from typing import Tuple, TYPE_CHECKING

from .data import regions as regiondata
from .data.encounters import encounter_types, encounters
from .locations import PokemonPlatinumLocation

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

def create_regions(world: "PokemonPlatinumWorld") -> Mapping[str, Region]:
    regions: Mapping[str, Region] = {}
    connections: Sequence[Tuple[str, str, str]] = []

    def setup_wild_regions(parent_region: Region, wild_region_data: regiondata.RegionData):
        header = wild_region_data.header
        if header not in encounters:
            return
        encs = encounters[wild_region_data.header]
        for type in encounter_types:
            if type not in wild_region_data.accessible_encounters:
                continue
            e = getattr(encs, type)
            name = f"{header}_{type}"
            if name not in regions:
                wild_region = Region(name, world.player, world.multiworld)
                regions[name] = wild_region

                for i, mon in enumerate(e):
                    location = PokemonPlatinumLocation(
                        world.player,
                        f"{name}_{i + 1}",
                        parent=wild_region,
                    )
                    location.show_in_spoiler = False
                    location.place_locked_item(world.create_event(f"mon_{mon}"))
                    wild_region.locations.append(location)
            else:
                wild_region = regions[name]
            parent_region.connect(wild_region, f"{parent_region.name} -> {name}")

    for region_name, region_data in regiondata.regions.items():
        new_region = Region(region_name, world.player, world.multiworld)

        regions[region_name] = new_region

        for event in region_data.events:
            event_loc = PokemonPlatinumLocation(
                world.player,
                event,
                parent=new_region)
            event_loc.show_in_spoiler = False
            event_loc.place_locked_item(world.create_event(event))
            new_region.locations.append(event_loc)

        setup_wild_regions(new_region, region_data)

        for region_exit in region_data.exits:
            connections.append((f"{region_name} -> {region_exit}", region_name, region_exit))

    for name, source, dest in connections:
        regions[source].connect(regions[dest], name)

    regions["Menu"] = Region("Menu", world.player, world.multiworld)
    regions["Menu"].connect(regions["twinleaf_town_player_house_2f"], "Start Game")

    return regions
