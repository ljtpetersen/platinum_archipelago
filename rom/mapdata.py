# rom/mapdata.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping

from ..apnds.narc import Narc

def replace_maps(map_narc_data: bytes, new_maps: Mapping[str, bytes]) -> bytes:
    narc = Narc.from_bytes(map_narc_data)
    for i_str, new_data in new_maps.items():
        narc.files[int(i_str)] = new_data
    return narc.to_bytes()

