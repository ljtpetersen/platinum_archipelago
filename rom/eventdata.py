# rom/eventdata.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, MutableSequence, Sequence
from dataclasses import dataclass, astuple, fields
from struct import pack, unpack_from
from typing import Any, Tuple

from ..apnds.narc import Narc

BOLLARD_GFX_ID = 192
CUT_TREE_GFX_ID = 86
ROCK_SMASH_GFX_ID = 85
STRENGTH_BOULDER_GFX_ID = 84
PSYDUCK_GFX_ID = 74

@dataclass
class BgEvent:
    script: int
    type: int
    x: int
    z: int
    y: int
    player_facing_dir: int

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "BgEvent":
        return BgEvent(*unpack_from("<2H3IH", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<2H3IH2x", *astuple(self))

@dataclass
class ObjectEvent:
    local_id: int
    graphics_id: int
    movement_type: int
    trainer_type: int
    flag: int
    script: int
    initial_dir: int
    data_0: int
    data_1: int
    data_2: int
    movement_range_x: int
    movement_range_z: int
    x: int
    z: int
    y: int

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "ObjectEvent":
        return ObjectEvent(*unpack_from("<14HI", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<14HI", *astuple(self))

@dataclass
class WarpEvent:
    x: int
    z: int
    dest_header_id: int
    dest_warp_id: int

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "WarpEvent":
        return WarpEvent(*unpack_from("<4H", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<4H4x", *astuple(self))

@dataclass
class CoordEvent:
    script: int
    x: int
    z: int
    width: int
    length: int
    y: int
    value: int
    var: int
    
    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "CoordEvent":
        return CoordEvent(*unpack_from("<8H", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<8H", *astuple(self))

@dataclass
class Events:
    bg_events: MutableSequence[BgEvent]
    object_events: MutableSequence[ObjectEvent]
    warp_events: MutableSequence[WarpEvent]
    coord_events: MutableSequence[CoordEvent]

    @staticmethod
    def from_bytes(data: bytes) -> "Events":
        offset = 0
        def get_events(clas, b_len: int):
            nonlocal offset
            num = int.from_bytes(data[offset:offset + 4], 'little')
            offset += 4
            ret = [clas.from_bytes(data, offset + b_len * i) for i in range(num)]
            offset += b_len * num
            return ret

        return Events(*(
            get_events(clas, b_len)
            for clas, b_len in [(BgEvent, 20), (ObjectEvent, 32), (WarpEvent, 12), (CoordEvent, 16)]
        ))

    def to_bytes(self) -> bytes:
        return b''.join(
            bts
            for field in fields(self)
            for bts in [len(getattr(self, field.name)).to_bytes(4, 'little'), *(v.to_bytes() for v in getattr(self, field.name))]
        )

def patch_events(events_data: bytes, patch_info: Mapping[str, Sequence[Tuple[str, Any]]]) -> bytes:
    narc = Narc.from_bytes(events_data)

    def replace_obj_field(obj: ObjectEvent, new_fields: Mapping[str, int]) -> None:
        for field, val in new_fields.items():
            setattr(obj, field, val)

    for idx_str, patches in patch_info.items():
        events = Events.from_bytes(narc.files[int(idx_str)])
        for patch, patch_data in patches:
            match patch:
                case "remove_objs_by_graphics_id":
                    events.object_events = [e for e in events.object_events if e.graphics_id != patch_data]
                case "replace_obj_fields_by_graphics_id":
                    for e in events.object_events:
                        if e.graphics_id == patch_data[0]:
                            replace_obj_field(e, patch_data[1])
                case _:
                    raise ValueError(f"unsupported events patch {patch}")
        narc.files[int(idx_str)] = events.to_bytes()

    return narc.to_bytes()
