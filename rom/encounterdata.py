# rom/encounterdata.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, MutableSequence, Sequence
from dataclasses import dataclass
from struct import pack, unpack_from

from ..apnds.narc import Narc

@dataclass
class GrassEncounter:
    level: int
    species: int

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "GrassEncounter":
        return GrassEncounter(*unpack_from("<B3xI", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<B3xI", self.level, self.species)

@dataclass
class GrassEncounters:
    encounter_rate: int
    encounters: Sequence[GrassEncounter]

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "GrassEncounters":
        encounter_rate, = unpack_from("<I", data, offset)
        encounters = [GrassEncounter.from_bytes(data, offset + 8 * i + 4) for i in range(12)]
        return GrassEncounters(encounter_rate, encounters)

    def to_bytes(self) -> bytes:
        return b''.join([
            pack("<I", self.encounter_rate),
            *[enc.to_bytes() for enc in self.encounters]
        ])

@dataclass
class WaterEncounter:
    min_level: int
    max_level: int
    species: int

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "WaterEncounter":
        return WaterEncounter(*unpack_from("<2b2xI", data, offset))

    def to_bytes(self) -> bytes:
        return pack("<2B2xI", self.min_level, self.max_level, self.species)


@dataclass
class WaterEncounters:
    encounter_rate: int
    encounters: Sequence[WaterEncounter]

    @staticmethod
    def from_bytes(data: bytes, offset: int) -> "WaterEncounters":
        encounter_rate, = unpack_from("<I", data, offset)
        encounters = [WaterEncounter.from_bytes(data, offset + 8 * i + 4) for i in range(5)]
        return WaterEncounters(encounter_rate, encounters)

    def to_bytes(self) -> bytes:
        return b''.join([
            pack("<I", self.encounter_rate),
            *[enc.to_bytes() for enc in self.encounters]
        ])


@dataclass
class Encounters:
    grass_encounters: GrassEncounters
    swarm_encounters: MutableSequence[int]
    day_encounters: MutableSequence[int]
    night_encounters: MutableSequence[int]
    radar_encounters: MutableSequence[int]
    encounter_rates_forms: MutableSequence[int]
    unown_table_id: int
    dual_slot_ruby_encounters: MutableSequence[int]
    dual_slot_sapphire_encounters: MutableSequence[int]
    dual_slot_emerald_encounters: MutableSequence[int]
    dual_slot_firered_encounters: MutableSequence[int]
    dual_slot_leafgreen_encounters: MutableSequence[int]
    surf_encounters: WaterEncounters
    unused: WaterEncounters
    old_rod_encounters: WaterEncounters
    good_rod_encounters: WaterEncounters
    super_rod_encounters: WaterEncounters

    @staticmethod
    def from_bytes(data: bytes) -> "Encounters":
        return Encounters(
            GrassEncounters.from_bytes(data, 0),
            list(unpack_from("<2I", data, 100)),
            list(unpack_from("<2I", data, 108)),
            list(unpack_from("<2I", data, 116)),
            list(unpack_from("<4I", data, 124)),
            list(unpack_from("<5I", data, 140)),
            unpack_from("<I", data, 160)[0],
            list(unpack_from("<2I", data, 164)),
            list(unpack_from("<2I", data, 172)),
            list(unpack_from("<2I", data, 180)),
            list(unpack_from("<2I", data, 188)),
            list(unpack_from("<2I", data, 196)),
            WaterEncounters.from_bytes(data, 204),
            WaterEncounters.from_bytes(data, 248),
            WaterEncounters.from_bytes(data, 292),
            WaterEncounters.from_bytes(data, 336),
            WaterEncounters.from_bytes(data, 380),
        )

    def to_bytes(self) -> bytes:
        return b''.join([
            self.grass_encounters.to_bytes(),
            pack("<2I", *self.swarm_encounters),
            pack("<2I", *self.day_encounters),
            pack("<2I", *self.night_encounters),
            pack("<4I", *self.radar_encounters),
            pack("<5I", *self.encounter_rates_forms),
            pack("<I", self.unown_table_id),
            pack("<2I", *self.dual_slot_ruby_encounters),
            pack("<2I", *self.dual_slot_sapphire_encounters),
            pack("<2I", *self.dual_slot_emerald_encounters),
            pack("<2I", *self.dual_slot_firered_encounters),
            pack("<2I", *self.dual_slot_leafgreen_encounters),
            self.surf_encounters.to_bytes(),
            self.unused.to_bytes(),
            self.old_rod_encounters.to_bytes(),
            self.good_rod_encounters.to_bytes(),
            self.super_rod_encounters.to_bytes(),
        ])

def patch_encounters(encounter_data: bytes, patch_info: Mapping[str, Mapping[str, Sequence[Sequence[int]]]]) -> bytes:
    narc = Narc.from_bytes(encounter_data)
    for id_str, table_maps in patch_info.items():
        id = int(id_str)
        data = Encounters.from_bytes(narc.files[id])
        for table, maps in table_maps.items():
            mp = {v[0]:v[1] for v in maps}
            if table == "land":
                for enc in data.grass_encounters.encounters:
                    if enc.species in mp:
                        enc.species = mp[enc.species]
                for key in ["swarm", "day", "night", "radar", "dual_slot_ruby", "dual_slot_sapphire", "dual_slot_emerald", "dual_slot_firered", "dual_slot_leafgreen"]:
                    seq: MutableSequence[int] = getattr(data, key + "_encounters")
                    for i, v in enumerate(seq):
                        if v in mp:
                            seq[i] = mp[v]
            else:
                encs: WaterEncounters = getattr(data, table + "_encounters")
                for enc in encs.encounters:
                    if enc.species in mp:
                        enc.species = mp[enc.species]
        narc.files[id] = data.to_bytes()
    return narc.to_bytes()

def patch_speencs(speenc_data: bytes, patch_info: Mapping[str, Sequence[Sequence[int]]]) -> bytes:
    narc = Narc.from_bytes(speenc_data)
    for id_str, maps in patch_info.items():
        id = int(id_str)
        data = narc.files[id]
        seq = list(unpack_from(f"<{len(data) // 4}I", data))
        mp = {v[0]:v[1] for v in maps}
        for i, v in enumerate(seq):
            if v in mp:
                seq[i] = mp[v]
        narc.files[id] = pack(f"<{len(data) // 4}I", *seq)
    return narc.to_bytes()
