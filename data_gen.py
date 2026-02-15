#!/usr/bin/env python3

# data_gen.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE


from dataclasses import dataclass, field
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Set, Sequence
from typing import Any, Tuple
import tomllib
from data_gen_rules import ItemConditions, RuleWithOpts, parse_rule
import re
import os

def default_accessible_encounters() -> Sequence[str]:
    return ["land", "water"]

def get_toml(name: str) -> Mapping[str, Any]:
    with open(f"data_gen/{name}.toml", "rb") as f:
        return tomllib.load(f)

def convert_frozenset(seq: Sequence[str]) -> str:
    return "frozenset({{{}}})".format(", ".join(map(lambda s : f'"{s}"', seq)))

def convert_list(seq: Sequence[str]) -> str:
    return "[{}]".format(", ".join(map(lambda s : f'"{s}"', seq)))

def convert_item_groups(group: str, items: Set[str]) -> Sequence[str]:
    ret = [f"{group}: {{\n"]
    ret += [f"    {item},\n" for item in items]
    ret.append("},\n")
    return ret

def convert_str(val: str) -> str:
    return f'"{val}"'

def identity(x):
    return x

def convert_level_learnset(val):
    return "[{}]".format(", ".join(f'({v[0]}, "{v[1]}")' for v in val))

@dataclass(frozen=True)
class Region:
    header: str
    exits: Sequence[str] = field(default_factory=list)
    locs: Sequence[str] = field(default_factory=list)
    events: Sequence[str] = field(default_factory=list)
    accessible_encounters: Sequence[str] = field(default_factory=default_accessible_encounters)
    group: str = "generic"
    honey_tree_idx: int | None = None
    special_encounters: str | None = None
    trainers: Sequence[str] = field(default_factory=list)

    def encounter_connection(self, type: str) -> str:
        return f"{self.header} -> {self.header}_{type}"

    def __str__(self) -> str:
        ret = f"RegionData(header=\"{self.header}\""
        convs = {
            "exits": convert_list,
            "events": convert_list,
            "trainers": convert_list,
            "accessible_encounters": convert_frozenset,
            "locs": convert_list,
            "honey_tree_idx": identity,
            "special_encounters": convert_str,
        }
        def is_nonempty(s) -> bool:
            return len(s) > 0
        def is_not_none(s) -> bool:
            return s is not None
        should_inc = {
            "exits": is_nonempty,
            "events": is_nonempty,
            "trainers": is_nonempty,
            "accessible_encounters": is_nonempty,
            "locs": is_nonempty,
            "honey_tree_idx": is_not_none,
            "special_encounters": is_not_none,
        }
        centre = ", ".join([f"{name}={convs[name](val)}"
            for name, val in map(lambda name : (name, getattr(self, name)),
                                  ["exits", "locs", "events", "accessible_encounters", "honey_tree_idx", "trainers", "special_encounters"])
            if should_inc[name](val)])
        if centre:
            centre = ", " + centre
        if self.group != "generic":
            centre += f", group=\"{self.group}\""
        return ret + centre + ")"

@dataclass(frozen=True)
class EncounterSlot:
    species: str
    level_lower: int
    level_upper: int
    accessibility: Sequence[str] = field(default_factory=list)

    def __str__(self) -> str:
        ret = f"EncounterSlot(species=\"{self.species}\", level_lower={self.level_lower}, level_upper={self.level_upper}"
        if self.accessibility:
            ret += f", accessibility={convert_list(self.accessibility)}"
        return ret + ")"


@dataclass(frozen=True)
class Encounters:
    id: int
    land: Sequence[EncounterSlot] = field(default_factory=list)
    surf: Sequence[EncounterSlot] = field(default_factory=list)
    old_rod: Sequence[EncounterSlot] = field(default_factory=list)
    good_rod: Sequence[EncounterSlot] = field(default_factory=list)
    super_rod: Sequence[EncounterSlot] = field(default_factory=list)

    def __str__(self) -> str:
        centre = ", ".join([f"id={self.id}"] + [f"{type}=[{', '.join(str(enc) for enc in encs)}]"
            for type, encs in map(lambda type : (type, getattr(self, type)),
                                  ["land", "surf", "old_rod", "good_rod", "super_rod"])
            if len(encs) > 0])

        return f"EncounterData({centre})"

@dataclass(frozen=True)
class Check:
    id: int
    value: int | None = None
    op: str = "eq"
    invert: bool = False
    once: bool = False

    def __str__(self) -> str:
        if self.once:
            assert self.value is None, f"once check has value"
            ret = f"OnceCheck(id=0x{self.id:X}"
            if self.invert:
                ret += ", invert=True"
            ret += ")"
            return ret
        elif self.value is None:
            ret = f"FlagCheck(id=0x{self.id:X}"
            if self.invert:
                ret += ", invert=True"
            ret += ")"
            return ret
        else:
            ret = f"VarCheck(id=0x{self.id:X}, value=0x{self.value:X}"
            if self.op != "eq":
                ret += f", op=operator.{self.op}"
            ret += ")"
            return ret

@dataclass(frozen=True)
class Location:
    original_item: str | Sequence[str]
    type: str
    table: str
    label: str
    id: int
    check: int | Check

    def to_string(self, parent_region: str | None) -> str:
        ret = f"LocationData(label=\"{self.label}\", "
        ret += f"table=LocationTable.{self.table.upper()}, "
        ret += f"id=0x{self.id:X}, "
        if isinstance(self.original_item, str):
            ret += f"original_item=\"{self.original_item}\", "
        else:
            ret += "original_item=[{}], ".format(", ".join(map(lambda s : f"\"{s}\"", self.original_item)))
        ret += f"type=\"{self.type}\", "
        if parent_region is not None:
            ret += f"parent_region=\"{parent_region}\", "
        check = self.check
        if isinstance(check, int):
            check = Check(check)
        ret += f"check={check})"
        return ret

@dataclass(frozen=True)
class Item:
    label: str
    id: int
    clas: str
    group: str
    classification: str = "filler"
    count: int | None = None
    data_id: int | None = None

    def __str__(self) -> str:
        ret = f"ItemData(label=\"{self.label}\", "
        ret += f"id=0x{self.id:X}, "
        ret += f"clas=ItemClass.{self.clas.upper()}"
        if self.count is not None and self.count != 1:
            ret += f", count={self.count}"
        if self.classification != "filler":
            ret += f", classification=ItemClassification.{self.classification}"
        if self.data_id is not None:
            ret += f", data_id={self.data_id}"
        ret += ")"
        return ret

@dataclass(frozen=True)
class RomInterface:
    loc_table: Mapping[str, int]
    item_clas: Mapping[str, int]
    hm: Mapping[str, str]
    hm_badge: Mapping[str, str]
    hm_tmhm_id: Mapping[str, int]
    item_group: Mapping[str, str]
    reusable_evo_items: Sequence[str]
    nonreusable_evo_items: Sequence[str]
    tm_of_move: Mapping[str, str]
    map_header_labels: Mapping[str, str]
    aux_reqd_items: Sequence[str]
    national_dex_requiring_encs: Sequence[str]

@dataclass(frozen=True)
class PreEvolution:
    species: str
    method: str
    level: int | None = None
    move: str | None = None
    item: str | None = None
    other_species: str | None = None

    def to_string(self, item_name_map: Callable[[str], str], tm_of_move: Mapping[str, str]) -> str:
        ret = f"PreEvolution(species=\"{self.species}\", method=\"{self.method}\""
        if self.level is not None:
            ret += f", level={self.level}"
        if self.move is not None:
            ret += f", item={item_name_map(tm_of_move[self.move])}"
        elif self.item is not None:
            ret += f", item={item_name_map(self.item)}"
        if self.other_species is not None:
            ret += f", other_species=\"{self.other_species}\""
        ret += ")"
        return ret

@dataclass(frozen=True)
class Species:
    hms: Sequence[str]
    id: int
    label: str
    level_learnset: Sequence[Tuple[int, str]]
    other_learnset: Sequence[str]
    regional: bool = False
    legendary: bool = False
    pre_evolution: PreEvolution | None = None

    def to_string(self, item_name_map: Callable[[str], str], tm_of_move: Mapping[str, str]) -> str:
        ret = f"SpeciesData(id={self.id}, label=\"{self.label}\", hms="
        if self.hms:
            ret += "{{{}}},".format(", ".join(map(lambda s : f"Hm.{s.upper()}", self.hms)))
        else:
            ret += "set(), "
        ret += f"level_learnset={convert_level_learnset(self.level_learnset)}, "
        ret += f"other_learnset={convert_list(self.other_learnset)}"
        
        if self.pre_evolution is not None:
            pre_ev = self.pre_evolution
            ret += f", pre_evolution={pre_ev.to_string(item_name_map, tm_of_move)}"
        ret += ")"

        return ret

@dataclass(frozen=True)
class Rules:
    exits: Mapping[str, Mapping[str, RuleWithOpts]] = field(default_factory=dict)
    encs: Mapping[str, Mapping[str, RuleWithOpts]] = field(default_factory=dict)
    locs: Mapping[str, RuleWithOpts] = field(default_factory=dict)
    events: Mapping[str, RuleWithOpts] = field(default_factory=dict)
    loc_types: Mapping[str, RuleWithOpts] = field(default_factory=dict)
    enc_types: Mapping[str, RuleWithOpts] = field(default_factory=dict)
    common: Mapping[str, RuleWithOpts] = field(default_factory=dict)
    trainers: Mapping[str, RuleWithOpts] = field(default_factory=dict)

@dataclass(frozen=True)
class PartyMember:
    species: str
    level: int
    num_moves: int

    def __str__(self) -> str:
        return f"PartyMember(species=\"{self.species}\", level={self.level}, num_moves={self.num_moves})"

@dataclass(frozen=True)
class Trainer:
    id: int
    label: str
    party: Sequence[PartyMember]
    requires_national_dex: bool = False
    check: Check | int | None = None

    def to_string(self, parent_region: str | None) -> str:
        ret = f"TrainerData(id={self.id}, label=\"{self.label}\", "
        ret += "party=[{}]".format(", ".join(str(p) for p in self.party))
        check = self.check
        if check is not None:
            if isinstance(check, int):
                check = Check(check)
            ret += f", check={check}"
        if parent_region is not None:
            ret += f", parent_region=\"{parent_region}\""
        if self.requires_national_dex:
            ret += f", requires_national_dex=True"
        return ret + ")"

@dataclass(frozen=True)
class SpecialEncounters:
    regular_honey_tree_encounters: Sequence[str]
    munchlax_honey_tree_encounters: Sequence[str]
    trophy_garden_daily_encounters: Sequence[str]
    great_marsh_observatory_encounters: Sequence[str]
    national_dex_great_marsh_observatory_encounters: Sequence[str]
    mt_coronet_b1f_elusive_fishing_encounters: Sequence[str]
    roamers: Sequence[str]
    odd_keystone: Sequence[str]

class ParserState:
    regions: Mapping[str, Region]
    encounters: Mapping[str, Encounters]
    locations: Mapping[str, Location]
    species: Mapping[str, Species]
    items: Mapping[str, Item]
    rom_interface: RomInterface
    rules: Rules
    trainers: Mapping[str, Trainer]
    special_encounters: SpecialEncounters
    moves: Mapping[str, int]
    event_checks: Mapping[str, Check]

    def __getattr__(self, name: str) -> Any:
        getattr(self, "parse_" + name)()
        return getattr(self, name)

    def parse_event_checks(self) -> None:
        def check_val(v: int | Mapping[str, Any]) -> Check:
            if isinstance(v, int):
                return Check(v)
            else:
                return Check(**v)
        self.event_checks = {k:check_val(v) for k, v in get_toml("event_checks").items()}

    def parse_regions(self):
        self.regions = {k:Region(**v) for k, v in get_toml("regions").items()}

    def parse_encounters(self):
        def convert_inner_encounter_slots(val: MutableMapping[str, Any]) -> Mapping[str, Sequence[EncounterSlot]]:
            for k, v in val.items():
                if k != "id":
                    val[k] = [EncounterSlot(**vp) for vp in v]
            return val
        self.encounters = {k:Encounters(**convert_inner_encounter_slots(v)) for k, v in get_toml("encounters").items()}

    def parse_items(self):
        self.items = {k:Item(**v) for k, v in get_toml("items").items()}

    def parse_locations(self):
        def convert_inner_check(val: MutableMapping[str, Any]) -> Mapping[str, Any]:
            check = val["check"]
            if not isinstance(check, int):
                val["check"] = Check(**check)
            return val
        self.locations = {k:Location(**convert_inner_check(v)) for k, v in get_toml("locations").items()}

    def parse_rom_interface(self):
        self.rom_interface = RomInterface(**get_toml("rom_interface"))

    def parse_species(self):
        def convert_inner_pre_evolution(val: MutableMapping[str, Any]) -> Mapping[str, Any]:
            if "pre_evolution" in val:
                val["pre_evolution"] = PreEvolution(**val["pre_evolution"])
            return val
        self.species = {k:Species(**convert_inner_pre_evolution(v)) for k, v in get_toml("species").items()}

    def parse_rules(self):
        def convert_rules(val):
            if isinstance(val, str):
                return parse_rule(val)
            else:
                for k in val:
                    val[k] = convert_rules(val[k])
                return val
        self.rules = Rules(**convert_rules(get_toml("rules"))) # type: ignore

    def parse_trainers(self):
        def convert_trainer(val):
            for k, v in enumerate(val["party"]):
                val["party"][k] = PartyMember(**v)
            if "check" in val:
                check = val["check"]
                if not isinstance(check, int):
                    val["check"] = Check(**check)
            return Trainer(**val)
        self.trainers = {k:convert_trainer(v) for k, v in get_toml("trainers").items()}

    def parse_special_encounters(self):
        self.special_encounters = SpecialEncounters(**get_toml("special_encounters"))

    def parse_moves(self):
        self.moves = get_toml("moves")

    def validate(self):
        loc_pairs = set()
        encounter_types = {"land", "water"}
        encounter_tables = ["land", "surf", "old_rod", "good_rod", "super_rod"]
        events = set()
        used_locs = set()
        for region in self.regions.values():
            for loc in region.locs:
                assert loc in self.locations, f"{loc} is a location"
                assert loc not in used_locs, f"{loc} is repeated"
                used_locs.add(loc)
            cur = set()
            for enc in region.accessible_encounters:
                assert enc in encounter_types, f"{enc} is an encounter type"
                assert enc not in cur, f"{enc} is repeated"
                cur.add(enc)
            cur = set()
            for exit in region.exits:
                assert exit in self.regions, f"{exit} is a region"
                assert exit not in cur, f"{exit} is repeated"
                cur.add(exit)
            for event in region.events:
                assert event not in events, f"{event} is a unique event"
                events.add(event)
            for trainer in region.trainers:
                if not trainer.startswith("rival_"):
                    assert trainer in self.trainers, f"{trainer} is a trainer"
        for encounter in self.encounters.values():
            for table in encounter_tables:
                for slot in getattr(encounter, table):
                    assert slot.species in self.species, f"{slot.species} is a species"
                    assert slot.level_lower <= slot.level_upper, f"encs: {slot.level_lower} <= {slot.level_upper}"
                    if table != "land":
                        assert len(slot.accessibility) == 0
                    for acc in slot.accessibility:
                        assert acc in {"radar", "ruby", "sapphire", "night", "emerald", "firered", "leafgreen", "day", "swarms"}, f"{acc} is an encounter slot accessibility"

        location_labels = set()
        for loc in self.locations.values():
            if isinstance(loc.original_item, str):
                assert loc.original_item in self.items, f"{loc.original_item} is an item"
            else:
                assert loc.original_item, f"{loc} has an original item"
                for original_item in loc.original_item:
                    assert original_item in self.items, f"{original_item} is an item"
            assert loc.table in self.rom_interface.loc_table, f"{loc.table} is a location table"
            assert loc.label not in location_labels, f"{loc.label} is a unique location label"
            location_labels.add(loc.label)
            assert loc.id >= 0, f"location id must be positive ({loc.label})"
            lp = (loc.table, loc.id)
            assert lp not in loc_pairs, f"location table+id {lp} is unique ({loc.label})"
            loc_pairs.add(lp)
            if isinstance(loc.check, Check):
                assert loc.check.op in ["eq", "ne", "lt", "le", "gt", "ge"]
        item_labels = set()
        item_classifications = {"filler", "progression", "useful"}
        for item in self.items.values():
            assert item.label not in item_labels, f"{item.label} is a unique item label"
            item_labels.add(item.label)
            assert item.clas in self.rom_interface.item_clas, f"{item.clas} is an item class"
            assert item.classification in item_classifications, f"{item.classification} is an item classification"
            if item.count is not None:
                assert item.clas == "bagitem", f"item {item.label} with count is not bag item"
        evo_items = set(self.rom_interface.reusable_evo_items) | set(self.rom_interface.nonreusable_evo_items)
        for spec in self.species.values():
            prev_hms = set()
            for hm in spec.hms:
                assert hm in self.rom_interface.hm, f"{hm} is a field move"
                assert hm not in prev_hms, f"repeated hm {hm}"
                prev_hms.add(hm)
            if spec.pre_evolution is not None:
                pe = spec.pre_evolution
                assert pe.species in self.species, f"{pe.species} is a species"
                mthd = pe.method
                assert mthd in {
                    "level",
                    "level_atk_gt_def",
                    "level_atk_eq_def",
                    "level_atk_lt_def",
                    "level_pid_low",
                    "level_pid_high",
                    "level_ninjask",
                    "level_shedinja",
                    "level_male",
                    "level_female",
                    "trade_with_held_item",
                    "use_item",
                    "use_item_male",
                    "use_item_female",
                    "level_with_held_item_day",
                    "level_with_held_item_night",
                    "level_happiness",
                    "level_happiness_day",
                    "level_happiness_night",
                    "trade",
                    "level_beauty",
                    "level_magnetic_field",
                    "level_moss_rock",
                    "level_ice_rock",
                    "level_know_move",
                    "level_species_in_party",
                }, f"{mthd} is an evolution method"
                if mthd in {
                        "level",
                        "level_atk_gt_def",
                        "level_atk_eq_def",
                        "level_atk_lt_def",
                        "level_pid_low",
                        "level_pid_high",
                        "level_ninjask",
                        "level_shedinja",
                        "level_male",
                        "level_female",
                    }:
                    assert pe.level is not None and pe.item is None and pe.move is None and pe.other_species is None, f"only level for method {mthd}"
                elif mthd in {
                        "trade_with_held_item",
                        "use_item",
                        "use_item_male",
                        "use_item_female",
                        "level_with_held_item_day",
                        "level_with_held_item_night",
                    }:
                    assert pe.level is None and pe.item is not None and pe.move is None and pe.other_species is None and pe.item in evo_items, f"only item for method {mthd}"
                elif mthd == "level_know_move":
                    assert pe.level is None and pe.item is None and pe.move is not None and pe.other_species is None and pe.move in self.rom_interface.tm_of_move, f"only move for method {mthd}"
                elif mthd == "level_species_in_party":
                    assert pe.level is None and pe.item is None and pe.move is None and pe.other_species is not None, f"only species for method {mthd}"
                else:
                    assert pe.level is None and pe.item is None and pe.move is None and pe.other_species is None, f"nothing for method {mthd}"
        for src, exits in self.rules.exits.items():
            assert src in self.regions, f"{src} is a region"
            for dest in exits:
                assert dest in self.regions[src].exits, f"{dest} is an exit of {src}"
                assert dest in self.regions, f"{dest} is a region"
        for region, rules in self.rules.encs.items():
            assert region in self.regions, f"{region} is a region"
            for type in rules:
                assert type in encounter_types, f"{type} is an encounter type"
        for loc in self.rules.locs:
            assert loc in self.locations, f"{loc} is a location"
        for event in self.rules.events:
            assert event in events, f"{event} is an event"
        for trainer in self.rules.trainers:
            if not trainer.startswith("rival_"):
                assert trainer in self.trainers, f"{trainer} is a trainer"
        trainer_ids = set()
        for trainer in self.trainers.values():
            if trainer.id in trainer_ids:
                assert f"{trainer.id} is a unique trainer id"
            if trainer.label in location_labels:
                assert f"{trainer.label} is a unique trainer, also among locatin labels"
            location_labels.add(trainer.label)
            trainer_ids.add(trainer.id)
            assert len(trainer.party) <= 6, "trainer party has at most 6 members"
            if trainer.check is not None and isinstance(trainer.check, Check):
                assert trainer.check.op in ["eq", "ne", "lt", "le", "gt", "ge"]
            for p in trainer.party:
                assert p.species in self.species, f"{p.species} is a species"
                assert p.level >= 1 and p.level <= 100, f"{p.level} is a valid level"

        for seq in [
            "regular_honey_tree_encounters",
            "munchlax_honey_tree_encounters",
            "trophy_garden_daily_encounters",
            "great_marsh_observatory_encounters",
            "national_dex_great_marsh_observatory_encounters",
            "mt_coronet_b1f_elusive_fishing_encounters",
            "roamers",
        ]:
            for spec in getattr(self.special_encounters, seq):
                assert spec in self.species, f"{spec} is a species"

        for item in self.rom_interface.tm_of_move.values():
            assert item in self.items, f"{item} is an item"
        for item in self.rom_interface.reusable_evo_items:
            assert item in self.items, f"{item} is an item"
        for item in self.rom_interface.nonreusable_evo_items:
            assert item in self.items, f"{item} is an item"

    def generate_items(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["ITEM_CLASSES"] = [f"{k.upper()} = 0x{v:X}\n" for k, v in self.rom_interface.item_clas.items()]
        ret["ITEMS"] = [f"\"{k}\": {v},\n" for k, v in self.items.items()]
        item_groups: Mapping[str, Set[str]] = {f"\"{label}\"":{f"\"{item.label}\""
            for item in self.items.values() if item.group == group}
            for group, label in self.rom_interface.item_group.items()}
        ret["ITEM_GROUPS"] = [l for group, items in item_groups.items()
            for l in convert_item_groups(group, items)]
        ret["REUSABLE_EVO_ITEMS"] = [f"{self.item_name_map(k)},\n" for k in self.rom_interface.reusable_evo_items]

        return ret

    def get_rule_items(self) -> ItemConditions:
        item_conds = ItemConditions()
        for exit_rules in self.rules.exits.values():
            for rule in exit_rules.values():
                rule.add_dependent_items(item_conds)
        for enc_rules in self.rules.encs.values():
            for rule in enc_rules.values():
                rule.add_dependent_items(item_conds)
        for rule in self.rules.locs.values():
            rule.add_dependent_items(item_conds)
        for rule in self.rules.loc_types.values():
            rule.add_dependent_items(item_conds)
        for rule in self.rules.enc_types.values():
            rule.add_dependent_items(item_conds)
        for rule in self.rules.common.values():
            rule.add_dependent_items(item_conds)
        for rule in self.rules.trainers.values():
            rule.add_dependent_items(item_conds)
        item_conds.add_all(self.rom_interface.hm.values())
        item_conds.add_all(self.rom_interface.hm_badge.values())
        item_conds.add_all(self.rom_interface.reusable_evo_items)
        item_conds.add_all(self.rom_interface.nonreusable_evo_items)
        item_conds.add_all(self.rom_interface.aux_reqd_items)
        item_conds.restrict(self.items.keys())
        return item_conds

    def generate_locations(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        location_region_map: Mapping[str, str] = {
            loc:name
            for name, region in self.regions.items()
            for loc in region.locs
        }
        
        ret["LOCATION_TABLES"] = [f"{k.upper()} = 0x{v:X}\n"
            for k, v in self.rom_interface.loc_table.items()]
        ret["LOCATIONS"] = [f"\"{k}\": {v.to_string(location_region_map.get(k))},\n" for k, v in self.locations.items()]
        rule_items = self.get_rule_items()
        req_locs: Mapping[str, MutableSequence[str]] = {}
        for k, v in self.locations.items():
            cond = rule_items.get_cond_str(v.original_item)
            if cond is not None:
                req_locs.setdefault(cond, []).append(k)
        req_locs_strs = []
        for cond, locs in req_locs.items():
            if cond == "True":
                pfx = ""
            else:
                pfx = "    "
                req_locs_strs.append(f"if {cond}:\n")
            if len(locs) == 1:
                req_locs_strs.append(f'{pfx}self.loc_rules.add("{locs[0]}")\n')
            else:
                req_locs_strs.append(f'{pfx}self.loc_rules |= {{\n')
                for k in locs:
                    req_locs_strs.append(f'{pfx}    "{k}",\n')
                req_locs_strs.append(f'{pfx}}}\n')
        ret["REQUIRED_LOCATIONS"] = req_locs_strs
        ret["MAXIMAL_REQUIRED_LOCATIONS"] = [f"\"{k}\",\n" for k, v in self.locations.items() if isinstance(v.original_item, str) and v.original_item in rule_items.base]

        return ret

    def generate_event_checks(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["EVENT_CHECKS"] = [f"\"{k}\": {v},\n" for k, v in self.event_checks.items()]

        return ret

    def generate_moves(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["MOVE_IDS"] = [f"\"{k}\": {v},\n" for k, v in self.moves.items()]

        return ret

    def get_item_set(self) -> Set[str]:
        return self.items.keys() | {event for region in self.regions.values() for event in region.events} | {f"mon_{spec}" for spec in self.species}

    def item_name_map(self, name: str) -> str:
        if name in self.items:
            return f"\"{self.items[name].label}\""
        else:
            return f"\"{name}\""

    def encounter_connection(self, region: str, type: str) -> str:
        return f"(\"{region}\", \"{self.regions[region].header}_{type}\")"

    def generate_rules(self) -> Mapping[str, Sequence[str]]:
        ret = {}
        item_set = self.get_item_set()

        ret["EXIT_RULES"] = [f"(\"{src}\", \"{dest}\"): {rule.to_string(item_set, self.item_name_map)},\n"
            for src, eles in self.rules.exits.items()
            for dest, rule in eles.items()]
        ret["EXIT_RULES"] += [f"{self.encounter_connection(region, type)}: {rule.to_string(item_set, self.item_name_map)},\n"
            for region, eles in self.rules.encs.items()
            for type, rule in eles.items()]

        accessible_locs = set()
        for region in self.regions.values():
            accessible_locs |= set(region.locs)
        ret["LOCATION_RULES"] = [f"\"{self.locations[loc].label}\": {rule.to_string(item_set, self.item_name_map)},\n"
            for loc, rule in self.rules.locs.items()
            if loc in accessible_locs]
        ret["LOCATION_RULES"] += [f"\"{event}\": {rule.to_string(item_set, self.item_name_map)},\n"
            for event, rule in self.rules.events.items()]
        
        ret["COMMON_RULES"] = [f"self.common_rules[\"{name}\"] = {rule.to_string(item_set, self.item_name_map)}\n"
                                for name, rule in self.rules.common.items()]

        ret["LOCATION_TYPE_RULES"] = [f"\"{type}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                      for type, rule in self.rules.loc_types.items()]
        ret["ENCOUNTER_TYPE_RULES"] = [f"\"{type}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                      for type, rule in self.rules.enc_types.items()]
        ret["TRAINER_RULES"] = [f"\"{tr}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                for tr, rule in self.rules.trainers.items()]

        return ret

    def generate___init__(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["HMS"] = [f"{hm.upper()} = \"{self.items[item].label}\"\n"
            for hm, item in self.rom_interface.hm.items()]
        ret["HM_BADGE_ITEMS"] = [f"case Hm.{hm.upper()}: return \"{self.items[item].label}\"\n"
                                 for hm, item in self.rom_interface.hm_badge.items()]
        ret["HM_TMHM_IDS"] = [f"case Hm.{hm.upper()}: return {id}\n"
                                 for hm, id in self.rom_interface.hm_tmhm_id.items()]
        ret["MAP_HEADER_LABELS"] = [f"\"{header}\": \"{label}\",\n"
                                 for header, label in self.rom_interface.map_header_labels.items()]

        return ret

    def generate_species(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["SPECIES"] = [f"\"{name}\": {spec.to_string(self.item_name_map, self.rom_interface.tm_of_move)},\n"
            for name, spec in self.species.items()]
        ret["REGIONAL_SPECIES"] = [f"\"{name}\",\n"
            for name, spec in self.species.items()
            if spec.regional]
        ret["LEGENDARY_SPECIES"] = [f"\"{name}\",\n"
            for name, spec in self.species.items()
            if spec.legendary]

        return ret

    def generate_encounters(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["ENCOUNTERS"] = [f"\"{name}\": {encs},\n" for name, encs in self.encounters.items()]
        ret["NATIONAL_DEX_REQUIRING_ENCS"] = [f"\"{hdr}\",\n" for hdr in self.rom_interface.national_dex_requiring_encs]

        return ret

    def generate_regions(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["REGIONS"] = [f"\"{name}\": {region},\n" for name, region in self.regions.items()]
        ret["EVENT_REGION_MAP"] = [f"\"{event}\": \"{name}\",\n"
            for name, region in self.regions.items()
            for event in region.events]

        return ret

    def generate_charmap(self) -> Mapping[str, Sequence[str]]:
        return {}

    def generate_trainers(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        def add_starter_rival(t):
            if t.startswith("rival_"):
                return t + "_turtwig"
            else:
                return t
        trainer_region_map: Mapping[str, str] = {
            add_starter_rival(trainer):name
            for name, region in self.regions.items()
            for trainer in region.trainers
        }
        ret["TRAINERS"] = [f"\"{k}\": {v.to_string(trainer_region_map.get(k))},\n" for k, v in self.trainers.items()]

        return ret

    def generate_special_encounters(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        for seq in [
            "regular_honey_tree_encounters",
            "munchlax_honey_tree_encounters",
            "trophy_garden_daily_encounters",
            "great_marsh_observatory_encounters",
            "national_dex_great_marsh_observatory_encounters",
            "mt_coronet_b1f_elusive_fishing_encounters",
            "roamers",
            "odd_keystone"
        ]:
            ret[seq.upper()] = [f"\"{v}\",\n" for v in getattr(self.special_encounters, seq)]

        return ret

def fill_template(name: str, values: Mapping[str, Sequence[str]]) -> None:
    output = f"# THIS IS AN AUTO-GENERATED FILE. DO NOT MODIFY.\n"
    with open(f"data_gen_templates/{name}.py", "r", encoding="utf-8") as template:
        for line in template:
            if line.strip().endswith("# TEMPLATE: DELETE"):
                continue
            matches = re.match(r"\s*", line)
            if matches is None:
                spaces = ""
            else:
                spaces = matches.group()
            prefix = spaces + "# TEMPLATE: "
            if not line.startswith(prefix):
                output += line
                continue
            kw = line.removeprefix(prefix).strip()
            if kw not in values:
                raise NameError(f"template has unknown keyword {kw}")
            for inner_line in values[kw]:
                output += spaces + inner_line
    with open(f"data/{name}.py", "w", encoding="utf-8") as f:
        f.write(output)

def main():
    try:
        os.mkdir("data")
    except FileExistsError:
        pass

    state = ParserState()
    state.validate()

    to_generate = [
        "items",
        "locations",
        "rules",
        "__init__",
        "species",
        "encounters",
        "regions",
        "charmap",
        "trainers",
        "special_encounters",
        "moves",
        "event_checks",
    ]
    for name in to_generate:
        fill_template(name, getattr(state, "generate_" + name)())

if __name__ == "__main__":
    main()
