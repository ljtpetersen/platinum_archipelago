# data_gen_templates/regions.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Set
from dataclasses import dataclass

@dataclass(frozen=True)
class RegionData:
    header: str
    exits: Set[str] = frozenset()
    locs: Set[str] = frozenset()
    events: Set[str] = frozenset()
    accessible_encounters: Set[str] = frozenset()
    group: str = "generic"

regions: Mapping[str, RegionData] = {
    # TEMPLATE: REGIONS
}

event_region_map: Mapping[str, str] = {
    # TEMPLATE: EVENT_REGION_MAP
}
