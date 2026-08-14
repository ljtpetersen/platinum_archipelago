
from collections.abc import Mapping, Sequence
from dataclasses import astuple, dataclass
from struct import pack, unpack
from typing import Any, Tuple

from ..apnds.narc import Narc

@dataclass
class MoveTable:
    effect: int
    clas: int
    power: int
    type: int
    accuracy: int
    pp: int
    effect_chance: int
    range: int
    priority: int
    flags: int
    contest_effect: int
    contest_type: int

    @staticmethod
    def from_bytes(data: bytes) -> "MoveTable":
        return MoveTable(*unpack("H6BHb3B2x", data))

    def to_bytes(self) -> bytes:
        return pack("<H6BHb3B2x", *astuple(self))

def patch_moves(pl_waza_tbl: bytes, patch_data: Mapping[str, Sequence[Tuple[str, Any]]]) -> bytes:
    narc = Narc.from_bytes(pl_waza_tbl)
    for id_str, patches in patch_data.items():
        move = MoveTable.from_bytes(narc.files[int(id_str)])
        for key, data in patches:
            if key.startswith("set_"):
                setattr(move, key[len("set_"):], data)
        narc.files[int(id_str)] = move.to_bytes()

    return narc.to_bytes()

