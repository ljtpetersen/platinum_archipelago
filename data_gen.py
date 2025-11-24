#!/usr/bin/env python3

# data_gen.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE


from dataclasses import dataclass, field
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Set, Sequence
from typing import Any
import tomllib
from data_gen_rules import ItemConditions, RuleWithOpts, parse_rule
import re
import os
import datetime

def default_accessible_encounters() -> Sequence[str]:
    return ["land", "surf", "old_rod", "good_rod", "super_rod"]

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

@dataclass(frozen=True)
class Region:
    exits: Sequence[str]
    header: str
    locs: Sequence[str] = field(default_factory=list)
    events: Sequence[str] = field(default_factory=list)
    accessible_encounters: Sequence[str] = field(default_factory=default_accessible_encounters)
    group: str = "generic"

    def encounter_connection(self, type: str) -> str:
        return f"{self.header} -> {self.header}_{type}"

    def __str__(self) -> str:
        ret = f"RegionData(header=\"{self.header}\""
        convs = {
            "exits": convert_list,
            "events": convert_list,
            "accessible_encounters": convert_frozenset,
            "locs": convert_list,
        }
        centre = ", ".join([f"{name}={convs[name](val)}"
            for name, val in map(lambda name : (name, getattr(self, name)),
                                  ["exits", "locs", "events", "accessible_encounters"])
            if val])
        if centre:
            centre = ", " + centre
        if self.group != "generic":
            centre += f", group=\"{self.group}\""
        return ret + centre + ")"


@dataclass(frozen=True)
class Encounters:
    land: Sequence[str] = field(default_factory=list)
    surf: Sequence[str] = field(default_factory=list)
    old_rod: Sequence[str] = field(default_factory=list)
    good_rod: Sequence[str] = field(default_factory=list)
    super_rod: Sequence[str] = field(default_factory=list)

    def __str__(self) -> str:
        centre = ", ".join([f"{type}={convert_list(encs)}"
            for type, encs in map(lambda type : (type, getattr(self, type)),
                                  ["land", "surf", "old_rod", "good_rod", "super_rod"])
            if encs])

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

    def __str__(self) -> str:
        ret = f"ItemData(label=\"{self.label}\", "
        ret += f"id=0x{self.id:X}, "
        ret += f"clas=ItemClass.{self.clas.upper()}"
        if self.count is not None and self.count != 1:
            ret += f", count={self.count}"
        if self.classification != "filler":
            ret += f", classification=ItemClassification.{self.classification}"
        ret += ")"
        return ret

@dataclass(frozen=True)
class RomInterface:
    loc_table: Mapping[str, int]
    item_clas: Mapping[str, int]
    hm: Mapping[str, str]
    hm_badge: Mapping[str, str]
    req_items: Sequence[str]
    item_group: Mapping[str, str]

@dataclass(frozen=True)
class PreEvolution:
    species: str
    item: str | None = None

    def to_string(self, item_name_map: Callable[[str], str]) -> str:
        ret = f"PreEvolution(species=\"{self.species}\""
        if self.item is not None:
            ret += f", item={item_name_map(self.item)}"
        ret += ")"
        return ret

@dataclass(frozen=True)
class Species:
    hms: Sequence[str]
    regional: bool = False
    pre_evolution: str | PreEvolution | None = None

    def to_string(self, item_name_map: Callable[[str], str]) -> str:
        ret = f"SpeciesData(hms="
        if self.hms:
            ret += "{{{}}}".format(", ".join(map(lambda s : f"Hm.{s.upper()}", self.hms)))
        else:
            ret += "set()"
        
        if self.pre_evolution is not None:
            pre_ev = self.pre_evolution
            if isinstance(pre_ev, str):
                pre_ev = PreEvolution(pre_ev)
            ret += f", pre_evolution={pre_ev.to_string(item_name_map)}"
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

class ParserState:
    regions: Mapping[str, Region]
    encounters: Mapping[str, Encounters]
    locations: Mapping[str, Location]
    species: Mapping[str, Species]
    items: Mapping[str, Item]
    rom_interface: RomInterface
    rules: Rules

    def __getattr__(self, name: str) -> Any:
        getattr(self, "parse_" + name)()
        return getattr(self, name)

    def parse_regions(self):
        self.regions = {k:Region(**v) for k, v in get_toml("regions").items()}

    def parse_encounters(self):
        self.encounters = {k:Encounters(**v) for k, v in get_toml("encounters").items()}

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
                pre_evol = val["pre_evolution"]
                if not isinstance(pre_evol, str):
                    val["pre_evolution"] = PreEvolution(**pre_evol)
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

    def validate(self):
        loc_pairs = set()
        encounter_types = {"land", "surf", "old_rod", "good_rod", "super_rod"}
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
        for encounter in self.encounters.values():
            for type in encounter_types:
                for spec in getattr(encounter, type):
                    assert spec in self.species, f"{spec} is a species"
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
        for spec in self.species.values():
            prev_hms = set()
            for hm in spec.hms:
                assert hm in self.rom_interface.hm, f"{hm} is a field move"
                assert hm not in prev_hms, f"repeated hm {hm}"
                prev_hms.add(hm)
            if spec.pre_evolution is not None:
                if isinstance(spec.pre_evolution, PreEvolution):
                    assert spec.pre_evolution.species in self.species, f"{spec.pre_evolution.species} is a species"
                    if spec.pre_evolution.item is not None:
                        assert spec.pre_evolution.item in self.items, f"{spec.pre_evolution.item} is an item"
                else:
                    assert spec.pre_evolution in self.species, f"{spec.pre_evolution} is a species"
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
        for req_item in self.rom_interface.req_items:
            assert req_item in self.items, f"{req_item} is an item"

    def generate_items(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["ITEM_CLASSES"] = [f"{k.upper()} = 0x{v:X}\n" for k, v in self.rom_interface.item_clas.items()]
        ret["ITEMS"] = [f"\"{k}\": {v},\n" for k, v in self.items.items()]
        item_groups: Mapping[str, Set[str]] = {f"\"{label}\"":{f"\"{item.label}\""
            for item in self.items.values() if item.group == group}
            for group, label in self.rom_interface.item_group.items()}
        ret["ITEM_GROUPS"] = [l for group, items in item_groups.items()
            for l in convert_item_groups(group, items)]

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
        item_conds.add_all(self.rom_interface.hm.values())
        item_conds.add_all(self.rom_interface.hm_badge.values())
        item_conds.add_all(self.rom_interface.req_items)
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
                req_locs_strs.append(f'{pfx}self.loc_rules.add("{locs[0]}")')
            else:
                req_locs_strs.append(f'{pfx}self.loc_rules |= {{\n')
                for k in locs:
                    req_locs_strs.append(f'{pfx}    "{k}",\n')
                req_locs_strs.append(f'{pfx}}}\n')
        ret["REQUIRED_LOCATIONS"] = req_locs_strs

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
        
        ret["COMMON_RULES"] = [f"\"{name}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                for name, rule in self.rules.common.items()]

        ret["LOCATION_TYPE_RULES"] = [f"\"{type}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                      for type, rule in self.rules.loc_types.items()]
        ret["ENCOUNTER_TYPE_RULES"] = [f"\"{type}\": {rule.to_string(item_set, self.item_name_map)},\n"
                                      for type, rule in self.rules.enc_types.items()]

        return ret

    def generate___init__(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["HMS"] = [f"{hm.upper()} = \"{self.items[item].label}\"\n"
            for hm, item in self.rom_interface.hm.items()]
        ret["HM_BADGE_ITEMS"] = [f"case Hm.{hm.upper()}: return \"{self.items[item].label}\"\n"
                                 for hm, item in self.rom_interface.hm_badge.items()]

        return ret

    def generate_species(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["SPECIES"] = [f"\"{name}\": {spec.to_string(self.item_name_map)},\n"
            for name, spec in self.species.items()]
        ret["REGIONAL_SPECIES"] = [f"\"{name}\",\n"
            for name, spec in self.species.items()
            if spec.regional]

        return ret

    def generate_encounters(self) -> Mapping[str, Sequence[str]]:
        ret = {}

        ret["ENCOUNTERS"] = [f"\"{name}\": {encs},\n" for name, encs in self.encounters.items()]

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

    to_generate = ["items", "locations", "rules", "__init__", "species", "encounters", "regions", "charmap"]
    for name in to_generate:
        fill_template(name, getattr(state, "generate_" + name)())

if __name__ == "__main__":
    main()
