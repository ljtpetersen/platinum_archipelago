# data_gen_templates/species.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from typing import Tuple
from . import Hm

@dataclass(frozen=True)
class PreEvolution:
    species: str
    method: str
    item: str | None = None
    level: int | None = None
    other_species: str | None = None

@dataclass(frozen=True)
class SpeciesData:
    hms: Set[Hm]
    id: int
    label: str
    level_learnset: Sequence[Tuple[int, str]]
    other_learnset: Sequence[str]
    pre_evolution: PreEvolution | None = None

species: Mapping[str, SpeciesData] = {
    # TEMPLATE: SPECIES
}

regional_mons: Sequence[str] = [
    # TEMPLATE: REGIONAL_SPECIES
]

legendary_mons: Sequence[str] = [
    # TEMPLATE: LEGENDARY_SPECIES
]

species_id_to_const_name: Mapping[int, str] = {v.id:k for k, v in species.items()}
