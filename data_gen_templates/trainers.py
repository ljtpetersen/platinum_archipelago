# data_gen_templates/trainers.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .locations import LocationCheck, VarCheck, FlagCheck, OnceCheck, LocationTable
from .regions import regions

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

def get_in_game_trainers() -> Sequence[str]:
    ret = set()
    for data in regions.values():
        ret |= set(data.trainers)
    return list(ret)

def remove_starter_suffix(s: str) -> str:
    return s.removesuffix("_piplup").removesuffix("_chimchar").removesuffix("_turtwig")

def add_starter_suffix(s: str) -> str:
    if s.startswith("lucas") or s.startswith("rival") or s.startswith("dawn"):
        return s + "_turtwig"
    else:
        return s

in_game_trainers: Sequence[str] = get_in_game_trainers()

in_game_trainer_labels: Sequence[str] = list({trainers[add_starter_suffix(v)].label for v in in_game_trainers})

trainer_name_to_trainer_const_name: Mapping[str, str] = {v.label:remove_starter_suffix(k) for k, v in trainers.items()}
