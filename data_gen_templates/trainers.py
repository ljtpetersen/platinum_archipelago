# data_gen_templates/trainers.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .locations import LocationCheck, VarCheck, FlagCheck, OnceCheck, LocationTable

@dataclass(frozen=True)
class TrainerCheck(LocationCheck):
    id: int

@dataclass(frozen=True)
class PartyMember:
    species: str
    level: int
    num_moves: int

@dataclass(frozen=True)
class TrainerData:
    id: int
    label: str
    party: Sequence[PartyMember]
    check: LocationCheck | None = None
    parent_region: str | None = None
    requires_national_dex: bool = False

    def get_raw_id(self) -> int:
        return LocationTable.TRAINERS << 16 | self.id

    def get_check(self) -> LocationCheck:
        if self.check is not None:
            return self.check
        else:
            return TrainerCheck(self.id)

trainers: Mapping[str, TrainerData] = {
    # TEMPLATE: TRAINERS
}

def trainer_party_supporting_starters(name: str) -> Sequence[PartyMember]:
    if name.startswith("lucas") or name.startswith("rival") or name.startswith("dawn"):
        return [memb
            for memb in trainers[name + "_piplup"].party
            if memb in trainers[name + "_chimchar"].party and memb in trainers[name + "_turtwig"].party
        ]
    else:
        return trainers[name].party

def trainer_requires_national_dex(name: str) -> bool:
    if name.startswith("lucas") or name.startswith("rival") or name.startswith("dawn"):
        return trainers[name + "_turtwig"].requires_national_dex
    else:
        return trainers[name].requires_national_dex

trainer_id_to_trainer_const_name: Mapping[int, str] = {v.id:k for k, v in trainers.items()}
