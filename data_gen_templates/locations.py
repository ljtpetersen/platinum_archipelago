
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

locations: Mapping[str, LocationData] = {
    # TEMPLATE: LOCATIONS
}

required_locations: Set[str] = frozenset({
    # TEMPLATE: REQUIRED_LOCATIONS
})
