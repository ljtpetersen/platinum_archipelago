# __init__.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from BaseClasses import CollectionState, ItemClassification, MultiWorld, Tutorial
from collections import defaultdict
from collections.abc import Iterable, Mapping, MutableMapping, MutableSequence, MutableSet, Sequence
import pkgutil
import settings
from typing import ClassVar, Any, Tuple
from worlds.AutoWorld import WebWorld, World

from .client import PokemonPlatinumClient
from .data import items as itemdata, rules as ruledata, Hm, species as speciesdata, regions as regiondata, trainers as trainerdata, map_header_labels
from .data.locations import RequiredLocations, LocationTable
from .items import create_item_label_to_code_map, get_item_classification, PokemonPlatinumItem, get_item_groups
from .locations import PokemonPlatinumLocation, create_location_label_to_code_map, create_locations
from .options import AddHMReader, OPTION_GROUPS, PokemonPlatinumOptions, RandomizeCartridges, RandomizeTimeItems
from .regions import create_regions
from .rom import generate_output, PokemonPlatinumPatch
from .rules import set_rules, verify_hm_accessibility
from .species import add_virt_specs, encounter_slot_label, fill_species, randomize_starters, randomize_trainer_parties_and_encounters, randomize_roamers, speenc_labels, roamer_labels

class PokemonPlatinumSettings(settings.Group):
    class RomFile(settings.UserFilePath):
        description = "Pokemon Platinum US (Rev 0 or 1) ROM File"
        copy_to = "pokeplatinum.nds"
        md5s = PokemonPlatinumPatch.hashes

    rom_file: RomFile = RomFile(RomFile.copy_to)

class PokemonPlatinumWebWorld(WebWorld):
    theme = 'ocean'

    setup_en = Tutorial(
        'Multiworld Setup Guide',
        'A guide to playing Pokémon Platinum with Archipelago',
        'English',
        'setup_en.md',
        'setup/en',
        ['ljtpetersen']
    )

    tutorials = [setup_en]

    option_groups = OPTION_GROUPS

class PokemonPlatinumWorld(World):
    game = "Pokemon Platinum"
    web = PokemonPlatinumWebWorld()
    topology_present = True

    settings_key = "pokemon_platinum_settings"
    settings: ClassVar[PokemonPlatinumSettings] # type: ignore

    options_dataclass = PokemonPlatinumOptions
    options: PokemonPlatinumOptions # type: ignore

    item_name_to_id = create_item_label_to_code_map()
    location_name_to_id = create_location_label_to_code_map()
    item_name_groups = get_item_groups()

    required_locations: RequiredLocations

    generated_starters: Tuple[str, str, str]
    generated_buneary: str
    generated_munchlax_trees: Tuple[int, int, int, int]
    # (map header, encounter table, index) -> species.
    generated_encounters: MutableMapping[Tuple[str, str, int], str]
    # (speenc, index) -> species
    generated_speencs: MutableMapping[Tuple[str, int], str]
    generated_roamers: Tuple[str, str, str, str, str]
    # (trainer, index) -> species
    generated_trainer_parties: MutableMapping[Tuple[str, int], str]
    dexsanity_specs: Sequence[str]
    trainersanity_trainers: Sequence[str]
    added_hm_compatibility: MutableMapping[str, MutableSequence[Hm]]

    accessible_mons: Sequence[str]
    accessible_once_mons: Sequence[str]
    accessible_see_mons: Sequence[str]

    ruledata: ruledata.Rules

    itempool: Sequence[PokemonPlatinumItem]

    seed: int

    def __init__(self, multiworld: MultiWorld, player: int) -> None:
        super().__init__(multiworld, player)
        self.generated_starters = ("turtwig", "chimchar", "piplup")
        self.generated_buneary = "buneary"
        self.generated_munchlax_trees = (0, 1, 2, 3)
        self.generated_encounters = {}
        self.generated_speencs = {}
        self.generated_trainer_parties = {}
        self.added_hm_compatibility = {}
        self.itempool = []


    def generate_early(self) -> None:
        if hasattr(self.multiworld, "generation_is_fake") \
            and hasattr(self.multiworld, "re_gen_passthrough") \
            and "Pokemon Platinum" in self.multiworld.re_gen_passthrough: # type: ignore
            slot_data: Mapping[str, Any] = self.multiworld.re_gen_passthrough["Pokemon Platinum"] # type: ignore
            self.seed = slot_data["seed"]
            self.options.load_options(slot_data)
        else:
            self.seed = self.random.getrandbits(64)
        self.random.seed(self.seed)

        self.required_locations = RequiredLocations(self.options)
        self.options.validate()

    def get_filler_item_name(self) -> str:
        # TODO
        return "Great Ball"

    def create_regions(self) -> None:
        self.generated_munchlax_trees = tuple(self.random.sample(list(range(21)), k=4)) # type: ignore
        regions, trainers = create_regions(self)

        randomize_starters(self)
        randomize_trainer_parties_and_encounters(self)
        randomize_roamers(self)
        add_virt_specs(self, regions)
        self.trainersanity_trainers = self.random.sample(sorted(trainers), k=self.options.trainersanity_count.value)
        create_locations(self, regions)
        self.multiworld.regions.extend(regions.values())

    def create_items(self) -> None:
        locations: Iterable[PokemonPlatinumLocation] = self.multiworld.get_locations(self.player) # type: ignore
        item_locations = filter(
            lambda loc : loc.address is not None and loc.is_enabled and not loc.locked,
            locations)

        add_items: list[str] = ["dragon_scale", "deepseatooth", "deepseascale", "honey_tree_upgrade", "feebas_upgrade"]
        for item in ["master_repel", "storage_key", "hm_reader"]:
            if getattr(self.options, item).value == 1:
                add_items.append(item)

        itempool = []
        for loc in item_locations:
            item_id: int = loc.default_item_id # type: ignore
            if item_id > 0 and get_item_classification(item_id) != ItemClassification.filler:
                itempool.append(self.create_item_by_code(item_id))
            elif len(add_items) > 0:
                itempool.append(self.create_item(itemdata.items[add_items.pop()].label))
            else:
                itempool.append(self.create_item_by_code(item_id))

        self.multiworld.itempool += itempool
        if self.options.hm_reader.value == AddHMReader.option_precollected:
            self.multiworld.push_precollected(self.create_item(itemdata.items["hm_reader"].label))
        for item in add_items:
            self.multiworld.push_precollected(self.create_item(itemdata.items[item].label))
        if self.options.cartridges == RandomizeCartridges.option_no_location:
            for cart in sorted(self.item_name_groups["GBA Cartridges"]):
                self.multiworld.push_precollected(self.create_item(cart))
        if self.options.time_items == RandomizeTimeItems.option_no_location:
            for item in sorted(self.item_name_groups["Time Items"]):
                self.multiworld.push_precollected(self.create_item(item))
        self.itempool = itempool

    def create_item(self, name: str) -> PokemonPlatinumItem:
        return self.create_item_by_code(self.item_name_to_id[name])

    def create_item_by_code(self, item_code: int):
        return PokemonPlatinumItem(
            self.item_id_to_name[item_code],
            get_item_classification(item_code),
            item_code,
            self.player)

    def set_rules(self) -> None:
        set_rules(self)

    def generate_output(self, output_directory: str) -> None:
        patch = PokemonPlatinumPatch(player=self.player, player_name=self.player_name)
        base_patches = ["us_rev0", "us_rev1"]
        for name in base_patches:
            name = "base_patch_" + name
            patch.write_file(f"{name}.bsdiff4", pkgutil.get_data(__name__, f"patches/{name}.bsdiff4")) # type: ignore
        generate_output(self, output_directory, patch)

    def create_event(self, name: str) -> PokemonPlatinumItem:
        return PokemonPlatinumItem(
            name,
            ItemClassification.progression,
            None,
            self.player)

    def generate_basic(self) -> None:
        fill_species(self)
        verify_hm_accessibility(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        ret = self.options.save_options()
        ret["seed"] = self.seed
        ret["dexsanity_specs"] = [speciesdata.species[spec].id for spec in self.dexsanity_specs]
        ret["trainersanity_trainers"] = [trainerdata.trainers[trainer + "_turtwig" if trainer.startswith("rival_") else trainer].get_raw_id() for trainer in self.trainersanity_trainers]
        ret["generated_encounters"] = {f"{region}_{table}_{i}":speciesdata.species[spec].id for (region, table, i), spec in self.generated_encounters.items()}
        ret["generated_special_encounters"] = {f"{speenc}_{i}":speciesdata.species[spec].id for (speenc, i), spec in self.generated_speencs.items()}
        ret["generated_roamers"] = [speciesdata.species[spec].id for spec in self.generated_roamers]
        ret["generated_starters"] = [speciesdata.species[spec].id for spec in self.generated_starters]
        ret["generated_trainer_parties"] = {f"{trainer}_{i}":speciesdata.species[spec].id for (trainer, i), spec in self.generated_trainer_parties.items()}
        ret["generated_munchlax_trees"] = list(self.generated_munchlax_trees)
        ret["added_hm_compatibility"] = {spec:[hm.name.lower() for hm in compat] for spec, compat in self.added_hm_compatibility.items()}
        ret["version"] = "0.2.0"
        return ret

    @staticmethod
    def interpret_slot_data(slot_data: Mapping[str, Any]) -> Mapping[str, Any]:
        return slot_data

    ut_can_gen_without_yaml = True

    def get_world_collection_state(self) -> CollectionState:
        state = CollectionState(self.multiworld, True)
        progression_items = [item for item in self.itempool if item.advancement]
        locations = self.get_locations()
        for item in progression_items:
            state.collect(item, True)
        for item in self.get_pre_fill_items():
            state.collect(item, True)
        state.sweep_for_advancements(locations)
        return state


    def extend_hint_information(self, hint_data: dict[int, dict[int, str]]) -> None:
        dexsanity_specs = set(self.dexsanity_specs)
        def get_dexsanity_encounter_hint_data(dexsanity_hint_data: MutableMapping[str, MutableSet[str]]) -> None:
            for key, mon in self.generated_encounters.items():
                if mon in dexsanity_specs:
                    dexsanity_hint_data[mon].add(encounter_slot_label(key, self.options.in_logic_encounters.value))

        #am_set = set(self.accessible_mons)
        #def get_dexsanity_evolution_hint_data(dexsanity_hint_data: dict[str, set[str]]) -> None:
        #    for mon in self.dexsanity_specs:
        #        data = speciesdata.species[mon]
        #        if data.pre_evolution is None \
        #            or data.pre_evolution.species not in am_set \
        #            or data.pre_evolution.method not in self.options.in_logic_evolution_methods \
        #            or data.pre_evolution.other_species is not None and data.pre_evolution.other_species not in am_set:
        #            continue
        #        dexsanity_hint_data[mon].add("Evolve from " + speciesdata.species[data.pre_evolution.species].label)

        player_hint_data = hint_data.setdefault(self.player, {})
        if self.options.dexsanity_count > 0:
            dexsanity_hint_data: dict[str, MutableSet[str]] = defaultdict(set)
            get_dexsanity_encounter_hint_data(dexsanity_hint_data)
            player_hint_data.update({
                speciesdata.species[mon].id | (LocationTable.DEX << 16):", ".join(methods)
                for mon, methods in dexsanity_hint_data.items()
            })

    def write_spoiler(self, spoiler_handle) -> None:
        spoiler_handle.write(f"\nPokemon Platinum ({self.player_name}):\n")
        spoiler_handle.write(f"\nHoney Tree Locations: {', '.join(map_header_labels[rd.header] for rd in regiondata.regions.values() if rd.honey_tree_idx in self.generated_munchlax_trees)}\n")

        if self.options.randomize_starters:
            spoiler_handle.write("Starters: {}\n".format(", ".join(speciesdata.species[spec].label for spec in self.generated_starters)))

        encounters_per_pokemon = defaultdict(set)
        if self.options.randomize_encounters:
            for key, mon in self.generated_encounters.items():
                encounters_per_pokemon[mon].add(encounter_slot_label(key, self.options.in_logic_encounters.value))
            for (speenc, _), mon in self.generated_speencs.items():
                encounters_per_pokemon[mon].add(speenc_labels[speenc])
        if self.options.randomize_roamers:
            for i, mon in enumerate(self.generated_roamers):
                encounters_per_pokemon[mon].add(roamer_labels[i])

        if encounters_per_pokemon:
            spoiler_handle.write(f"\nRandomized Pokemon ({self.player_name}):\n")
            lines = [f"{speciesdata.species[mon].label}: {', '.join(locations)}\n"
                     for mon, locations in encounters_per_pokemon.items()]
            lines.sort()
            spoiler_handle.writelines(lines)
