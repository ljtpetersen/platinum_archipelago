# data_gen_templates/locations.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Callable, Mapping, Sequence, Set
from dataclasses import dataclass
from enum import IntEnum
import operator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..options import PokemonPlatinumOptions

class LocationTable(IntEnum):
    # TEMPLATE: LOCATION_TABLES
    pass # TEMPLATE: DELETE

class LocationCheck:
    pass

@dataclass(frozen=True)
class VarCheck(LocationCheck):
    id: int
    value: int
    op: Callable[[int, int], bool] = operator.eq

@dataclass(frozen=True)
class FlagCheck(LocationCheck):
    id: int
    invert: bool = False

@dataclass(frozen=True)
class OnceCheck(LocationCheck):
    id: int
    invert: bool = False

@dataclass(frozen=True)
class LocationData:
    label: str
    table: LocationTable
    id: int
    original_item: str | Sequence[str]
    type: str
    check: LocationCheck
    parent_region: str | None = None

    def get_raw_id(self) -> int:
        return self.table << 16 | self.id

locations: Mapping[str, LocationData] = {
    # TEMPLATE: LOCATIONS
}

class RequiredLocations:
    opts: "PokemonPlatinumOptions"
    loc_rules: Set[str]

    def __init__(self, opts: "PokemonPlatinumOptions"):
        self.opts = opts
        self.loc_rules = set()
        # TEMPLATE: REQUIRED_LOCATIONS

    def __contains__(self, loc: str) -> bool:
        return loc in self.loc_rules


maximal_required_locations: Set[str] = {
    # TEMPLATE: MAXIMAL_REQUIRED_LOCATIONS
    "" # TEMPLATE: DELETE
}
