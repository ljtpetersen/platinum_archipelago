# data_gen_templates/moves.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, IntFlag

from .species import PokemonType

class MoveClass(IntEnum):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: MOVE_CLASSES

class MoveBattleEffect(IntEnum):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: MOVE_BATTLE_EFFECTS

    def has_chance(self) -> bool:
        return self in {
            MoveClass.DUMMY # TEMPLATE: DELETE
            # TEMPLATE: MOVE_BATTLE_EFFECTS_WITH_CHANCE
        }

class MoveRange(IntEnum):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: MOVE_RANGES

class MoveFlag(IntFlag):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: MOVE_FLAGS

class MoveContestEffect(IntEnum):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: MOVE_CONTEST_EFFECTS

class ContestType(IntEnum):
    DUMMY = 0 # TEMPLATE: DELETE
    # TEMPLATE: CONTEST_TYPES

@dataclass(frozen=True)
class MoveEffect:
    type: MoveBattleEffect
    chance: int = 0

@dataclass(frozen=True)
class MoveContest:
    type: ContestType
    effect: MoveContestEffect

@dataclass(frozen=True)
class Move:
    id: int
    name: str
    clas: MoveClass
    description: Sequence[str]
    type: PokemonType
    power: int
    pp: int
    effect: MoveEffect
    contest: MoveContest
    range: MoveRange = MoveRange.SINGLE_TARGET
    priority: int = 0
    accuracy: int = 100
    flags: MoveFlag = MoveFlag(0)

moves: Mapping[str, Move] = {
    # TEMPLATE: MOVES
}
