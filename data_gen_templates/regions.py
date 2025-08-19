from collections.abc import Mapping, Set
from dataclasses import dataclass

@dataclass(frozen=True)
class RegionData:
    header: str
    exits: Set[str] = frozenset()
    locs: Set[str] = frozenset()
    events: Set[str] = frozenset()
    accessible_encounters: Set[str] = frozenset()

regions: Mapping[str, RegionData] = {
    # TEMPLATE: REGIONS
}

