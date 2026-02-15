# data_gen_templates/encounters.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, field
from typing import Tuple

@dataclass(frozen=True)
class EncounterSlot:
    species: str
    level_lower: int
    level_upper: int
    accessibility: Sequence[str] = field(default_factory=list)

@dataclass(frozen=True)
class EncounterData:
    id: int
    land: Sequence[EncounterSlot] = field(default_factory=list)
    surf: Sequence[EncounterSlot] = field(default_factory=list)
    good_rod: Sequence[EncounterSlot] = field(default_factory=list)
    old_rod: Sequence[EncounterSlot] = field(default_factory=list)
    super_rod: Sequence[EncounterSlot] = field(default_factory=list)

encounters: Mapping[str, EncounterData] = {
    # TEMPLATE: ENCOUNTERS
}

encounter_type_pairs: Sequence[Tuple[str, str]] = [
    ("land", "land"),
    ("water", "surf"),
    ("water", "old_rod"),
    ("water", "good_rod"),
    ("water", "super_rod"),
]

encounter_type_tables: Mapping[str, Sequence[str]] = {
    "land": ["land"],
    "water": ["surf", "old_rod", "good_rod", "super_rod"],
}

national_dex_requiring_encs: Set[str] = {
    # TEMPLATE: NATIONAL_DEX_REQUIRING_ENCS
    "" # TEMPLATE: DELETE
}
