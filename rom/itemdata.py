
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from ..apnds.narc import Narc

class ItemDataField(Enum):
    PREVENT_TOSS = (69, 70)

    def __len__(self) -> int:
        l, u = self.value
        return u - l

@dataclass
class ItemData:
    data: bytearray

    def __getitem__(self, field: ItemDataField | Tuple[int, int]) -> int:
        # we hate bitfield
        # this function may or may not work.
        if isinstance(field, ItemDataField):
            l, u = field.value
        else:
            l, u = field
        ret = self.data[l // 8] >> (l & 7)
        if u - l < 8:
            ret &= (1 << (u - l)) - 1
        bts = 8 - (l & 7)
        lb = l // 8 + 1
        ub = u // 8
        if ub - lb >= 1:
            ret |= int.from_bytes(self.data[lb:ub], 'little') << bts
        if u & 7 != 0:
            ret |= (self.data[ub] & ((1 << (u & 7)) - 1)) << bts
        return ret

    def __setitem__(self, field: ItemDataField | Tuple[int, int], value: int) -> None:
        # this function may or may not work.
        if isinstance(field, ItemDataField):
            l, u = field.value
        else:
            l, u = field
        if l // 8 == u // 8:
            self.data[l // 8] = self.data[l // 8] & (((1 << (l & 7)) - 1) | (((1 << (8 - (u & 7))) - 1) << (u & 7))) | ((value & ((1 << (u - l)) - 1)) << (l & 7))
            return
        self.data[l // 8] = self.data[l // 8] & ((1 << (l & 7)) - 1) | ((value & ((1 << (8 - (l & 7))) - 1)) << (l & 7))
        value >>= l & 7
        lb = l // 8 + 1
        ub = u // 8
        if ub - lb >= 1:
            self.data[lb:ub] = (value & ((1 << ((ub - lb) * 8)) - 1)).to_bytes(ub - lb, 'little')
            value >>= (ub - lb) * 8
        self.data[ub] = self.data[ub] & (((1 << (8 - (u & 7))) - 1) << (u & 7)) | value & ((1 << (u & 7)) - 1)

def patch_items(pl_item_data: bytes, patch_info: Mapping[str, Sequence[Tuple[str, int]]]) -> bytes:
    narc = Narc.from_bytes(pl_item_data)
    for id, patches in patch_info.items():
        id = int(id)
        item_data = ItemData(bytearray(narc.files[id]))
        for field, val in patches:
            item_data[getattr(ItemDataField, field)] = val
        narc.files[id] = bytes(item_data.data)
    return narc.to_bytes()

