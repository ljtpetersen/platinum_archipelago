from collections.abc import Mapping, Set
from dataclasses import dataclass

@dataclass(frozen=True)
class EncounterData:
    land: Set[str] = frozenset()
    surf: Set[str] = frozenset()
    good_rod: Set[str] = frozenset()
    old_rod: Set[str] = frozenset()
    super_rod: Set[str] = frozenset()

encounters: Mapping[str, EncounterData] = {
    # TEMPLATE: ENCOUNTERS
}
