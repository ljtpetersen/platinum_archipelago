# rom/trainerdata.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence
from struct import pack_into, unpack_from
from typing import Any

from ..apnds.narc import Narc

PARTY_MEMB_STRUCT_SIZES = [8, 16, 10, 18]

def patch_trainer_parties(trainer_data: bytes, trainer_party_data: bytes, patch_info: Mapping[str, Sequence[Mapping[str, Any]]]) -> bytes:
    trdata = Narc.from_bytes(trainer_data)
    narc = Narc.from_bytes(trainer_party_data)

    for id_str, new_party in patch_info.items():
        id = int(id_str)
        mon_data_type, = unpack_from("<B", trdata.files[id])
        party_data = bytearray(narc.files[id])
        sz = PARTY_MEMB_STRUCT_SIZES[mon_data_type]
        for i, data in enumerate(new_party):
            pack_into("<2H", party_data, sz * i + 2, data["level"], data["species"])
            mvs = data["moves"]
            if mvs:
                pack_into("<4H", party_data, sz * i + (6 if mon_data_type == 1 else 8), *(mvs + [0] * (4 - len(mvs))))
        narc.files[id] = bytes(party_data)
    return narc.to_bytes()
