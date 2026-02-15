# rom/speciesdata.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence
from typing import Any

from ..apnds.narc import Narc

FORM_NARC_IDXS: Mapping[int, Sequence[int]] = {
    386: [386, 496, 497, 498],
    413: [413, 499, 500],
    487: [487, 501],
    492: [492, 502],
    479: [479, 503, 504, 505, 506, 507],
}

def patch_species(species_data: bytes, patch_info: Mapping[str, Mapping[str, Any]]) -> bytes:
    narc = Narc.from_bytes(species_data)
    def all_narc_idxs(spec_id: int) -> Sequence[int]:
        return FORM_NARC_IDXS.get(spec_id, [spec_id])
    def add_tmhm_compat(spec_id: int, tmhm_ids: Sequence[int]) -> None:
        for id in all_narc_idxs(spec_id):
            bt = bytearray(narc.files[id])
            for tmhm_id in tmhm_ids:
                bt[28 + (tmhm_id >> 3)] |= 1 << (tmhm_id & 7)
            narc.files[id] = bytes(bt)
    for spec_str, patches in patch_info.items():
        spec = int(spec_str)
        for patch, patch_data in patches.items():
            match patch:
                case "add_tmhm_compat":
                    add_tmhm_compat(spec, patch_data)
                case _:
                    raise ValueError(f"unsupported species patch {patch}")
    return narc.to_bytes()
