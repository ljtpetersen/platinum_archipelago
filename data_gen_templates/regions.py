# data_gen_templates/regions.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, field

@dataclass(frozen=True)
class RegionData:
    header: str
    exits: Sequence[str] = field(default_factory=list)
    locs: Sequence[str] = field(default_factory=list)
    events: Sequence[str] = field(default_factory=list)
    accessible_encounters: Set[str] = frozenset()
    group: str = "generic"
    trainers: Sequence[str] = field(default_factory=list)
    honey_tree_idx: int | None = None
    special_encounters: str | None = None
    roamers: Sequence[int] | None = None

regions: Mapping[str, RegionData] = {
    # TEMPLATE: REGIONS
}

event_region_map: Mapping[str, str] = {
    # TEMPLATE: EVENT_REGION_MAP
}
