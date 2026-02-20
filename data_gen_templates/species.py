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

def make_evolution_map() -> Mapping[str, Sequence[str]]:
    ret = {}
    for name, spec in species.items():
        if spec.pre_evolution:
            from_spec = spec.pre_evolution.species 
            if from_spec not in ret:
                ret[from_spec] = [name]
            else:
                ret[from_spec].append(name)
    return ret

evolutions: Mapping[str, Sequence[str]] = make_evolution_map()

def get_two_level_evo_species() -> Set[str]:
    def has_two_level_evo(spec: str) -> bool:
        for _ in range(2):
            for evo_to in evolutions.get(spec, []):
                pevo = species[evo_to].pre_evolution
                if pevo.method == "level": # type: ignore
                    spec = evo_to
                    break
            else:
                return False
        else:
            return True
    return {spec for spec in species if has_two_level_evo(spec)}

having_two_level_evos: Set[str] = get_two_level_evo_species()
