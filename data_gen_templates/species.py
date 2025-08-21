
from collections.abc import Mapping, Set
from dataclasses import dataclass
from . import Hm

@dataclass(frozen=True)
class PreEvolution:
    species: str
    item: str | None = None

@dataclass(frozen=True)
class SpeciesData:
    hms: Set[Hm]
    pre_evolution: PreEvolution | None = None

species: Mapping[str, SpeciesData] = {
    # TEMPLATE: SPECIES
}

regional_mons: Set[str] = frozenset({
    # TEMPLATE: REGIONAL_SPECIES
})
