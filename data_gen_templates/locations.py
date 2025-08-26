# data_gen_templates/locations.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Callable, Mapping, Set
from dataclasses import dataclass
from enum import IntEnum
import operator

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
class LocationData:
    label: str
    table: LocationTable
    id: int
    original_item: str
    type: str
    check: LocationCheck
    parent_region: str | None = None

    def get_raw_id(self) -> int:
        return self.table << 16 | self.id

locations: Mapping[str, LocationData] = {
    # TEMPLATE: LOCATIONS
}

required_locations: Set[str] = frozenset({
    # TEMPLATE: REQUIRED_LOCATIONS
})
