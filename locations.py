# locations.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import ItemClassification, Location, Region
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

from .data import items as itemdata, locations as locationdata, regions as regiondata, trainers as trainerdata, species as speciesdata
from .options import PokemonPlatinumOptions, RandomizeKeyItems, RemoteItems, UnownsOption

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

raw_id_to_const_name = { loc.get_raw_id():name for name, loc in locationdata.locations.items() }

@dataclass(frozen=True)
class LocationType:
    is_enabled: Callable[[PokemonPlatinumOptions], bool]
    should_be_added: Callable[[PokemonPlatinumOptions], bool] = lambda _ : True

location_types: Mapping[str, LocationType] = {
    "overworld": LocationType(is_enabled = lambda opts : opts.overworlds.value == 1),
    "hidden": LocationType(is_enabled = lambda opts : opts.hiddens.value == 1),
    "hm": LocationType(is_enabled = lambda opts : opts.hms.value == 1),
    "badge": LocationType(is_enabled = lambda opts : opts.badges.value == 1),
    "key_item": LocationType(is_enabled = lambda opts : opts.key_items.are_most_randomized()),
    "all_key_item": LocationType(is_enabled = lambda opts : opts.key_items.value == RandomizeKeyItems.option_all),
    "npc_gift": LocationType(is_enabled = lambda opts : opts.npc_gifts.value == 1),
    "rod": LocationType(is_enabled = lambda opts : opts.rods.value == 1),
    "poketchapp": LocationType(is_enabled = lambda opts : opts.poketch_apps.value == 1),
    "running_shoes": LocationType(is_enabled = lambda opts : opts.running_shoes.value == 1),
    "bicycle": LocationType(is_enabled = lambda opts : opts.bicycle.value == 1),
    "pokedex": LocationType(is_enabled = lambda opts : opts.pokedex.value == 1),
    "uunown": LocationType(
        is_enabled = lambda opts : opts.hiddens.value == 1 and opts.unown_option.value == UnownsOption.option_item,
        should_be_added = lambda opts : opts.unown_option == UnownsOption.option_item
    ),
    "accessory": LocationType(is_enabled = lambda opts : opts.accessories.value == 1),
    "bag": LocationType(is_enabled = lambda opts : opts.bag.value == 1),
    "cartridge": LocationType(
        is_enabled = lambda opts : opts.cartridges.value == 1,
        should_be_added = lambda opts : opts.cartridges.value != 2,
    ),
    "time_item": LocationType(
        is_enabled = lambda opts : opts.time_items.value == 1,
        should_be_added = lambda opts : opts.time_items.value != 2,
    ),
    "s_s_ticket": LocationType(is_enabled = lambda opts : opts.s_s_ticket.value == 1),
    "marsh_pass": LocationType(
        is_enabled = lambda opts : opts.marsh_pass == 1,
        should_be_added = lambda opts : opts.marsh_pass == 1
    ),
}

def get_parent_region(label: str, world: "PokemonPlatinumWorld") -> str | None:
    const_name = raw_id_to_const_name[world.location_name_to_id[label]]
    return locationdata.locations[const_name].parent_region

def remote_items_should_add(const_name: str, world: "PokemonPlatinumWorld") -> bool:
    if world.options.remote_items == RemoteItems.option_all:
        return True
    elif world.options.remote_items == RemoteItems.option_only_randomized_or_progression:
        orig_item = locationdata.locations[const_name].original_item
        if not isinstance(orig_item, str):
            return False
        if itemdata.items[orig_item].classification == ItemClassification.progression:
            return True
    return False

def is_location_in_world(label: str, world: "PokemonPlatinumWorld") -> bool:
    const_name = raw_id_to_const_name[world.location_name_to_id[label]]
    lt = location_types[locationdata.locations[const_name].type]
    if not lt.should_be_added(world.options):
        return False
    if lt.is_enabled(world.options) or const_name in world.required_locations:
        return True
    return remote_items_should_add(const_name, world)

def create_location_label_to_code_map() -> Dict[str, int]:
    id_map = {}
    id_map.update({v.label:v.get_raw_id() for v in locationdata.locations.values()})
    id_map.update({"Trainersanity - " + v.label:v.get_raw_id() for v in trainerdata.trainers.values()})
    id_map.update({"Dexsanity - " + v.label:v.id | (locationdata.LocationTable.DEX << 16) for v in speciesdata.species.values()})
    return id_map

class PokemonPlatinumLocation(Location):
    game: str = "Pokemon Platinum"
    type: str
    default_item_id: int | None
    is_enabled: bool

    def __init__(
        self,
        player: int,
        name: str,
        type: str,
        address: int | None = None,
        parent: Region | None = None,
        default_item_id: int | None = None,
        is_enabled: bool = True,
    ) -> None:
        super().__init__(player, name, address, parent)
        self.default_item_id = default_item_id
        self.is_enabled = is_enabled
        self.type = type

def create_locations(world: "PokemonPlatinumWorld", regions: Mapping[str, Region]) -> None:
    for region_name, region_data in regiondata.regions.items():
        if region_name not in regions:
            continue
        region = regions[region_name]
        for name in region_data.locs:
            loc = locationdata.locations[name]
            lt = location_types[loc.type]
            is_enabled = lt.is_enabled(world.options)
            if not is_location_in_world(loc.label, world):
                continue
            if isinstance(loc.original_item, str):
                original_item = loc.original_item
            else:
                original_item = world.random.choice(loc.original_item)
            item = itemdata.items[original_item]
            isnt_event = remote_items_should_add(name, world)
            if is_enabled or isnt_event:
                address = loc.get_raw_id()
            else:
                address = None
            plat_loc = PokemonPlatinumLocation(
                world.player,
                loc.label,
                loc.type,
                address=address,
                parent=region,
                default_item_id=item.get_raw_id(),
                is_enabled=is_enabled)
            if not is_enabled:
                if isnt_event:
                    ap_item = world.create_item(item.label)
                else:
                    ap_item = world.create_event(item.label)
                plat_loc.place_locked_item(ap_item)
                plat_loc.show_in_spoiler = False
            region.locations.append(plat_loc)
        if world.options.trainersanity:
            for name in region_data.trainers:
                if name.startswith("rival_"):
                    name += "_turtwig"
                tr = trainerdata.trainers[name]
                original_item = world.random.choice(["star_piece", "nugget"])
                item = itemdata.items[original_item]
                address = tr.get_raw_id()
                plat_loc = PokemonPlatinumLocation(
                    world.player,
                    "Trainersanity - " + tr.label,
                    "trainersanity",
                    address=address,
                    parent=region,
                    default_item_id=item.get_raw_id(),
                    is_enabled=True)
                region.locations.append(plat_loc)

    rgms = set(speciesdata.regional_mons)
    balls = sorted(world.item_name_groups["Balls"])
    dex_reg = regions["virt_dex"]
    national_dex_reg = regions["virt_national_dex"]
    for spec in world.dexsanity_specs:
        if spec in rgms:
            region = dex_reg
        else:
            region = national_dex_reg
        plat_loc = PokemonPlatinumLocation(
            world.player,
            "Dexsanity - " + speciesdata.species[spec].label,
            "dexsanity",
            address=speciesdata.species[spec].id | (locationdata.LocationTable.DEX << 16),
            parent=region,
            default_item_id=world.item_name_to_id[world.random.choice(balls)],
            is_enabled=True)
        region.locations.append(plat_loc)
