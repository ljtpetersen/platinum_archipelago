# data_gen_templates/encounters.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, field

@dataclass(frozen=True)
class EncounterData:
    land: Sequence[str] = field(default_factory=list)
    surf: Sequence[str] = field(default_factory=list)
    good_rod: Sequence[str] = field(default_factory=list)
    old_rod: Sequence[str] = field(default_factory=list)
    super_rod: Sequence[str] = field(default_factory=list)

encounters: Mapping[str, EncounterData] = {
    # TEMPLATE: ENCOUNTERS
}

# because sometimes we need inclusion and sometimes we need iteration,
# but iteration needs to be deterministic
encounter_types_seq: Sequence[str] = ["land", "surf", "good_rod", "old_rod", "super_rod"]
encounter_types: Set[str] = frozenset(encounter_types_seq)
