# data_gen_templates/special_encounters.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Sequence, Set

regular_honey_tree: Sequence[str] = [
    # TEMPLATE: REGULAR_HONEY_TREE_ENCOUNTERS
]

munchlax_honey_tree: Sequence[str] = [
    # TEMPLATE: MUNCHLAX_HONEY_TREE_ENCOUNTERS
]

trophy_garden: Sequence[str] = [
    # TEMPLATE: TROPHY_GARDEN_DAILY_ENCOUNTERS
]

great_marsh_observatory: Sequence[str] = [
    # TEMPLATE: GREAT_MARSH_OBSERVATORY_ENCOUNTERS
]

great_marsh_observatory_national_dex: Sequence[str] = [
    # TEMPLATE: NATIONAL_DEX_GREAT_MARSH_OBSERVATORY_ENCOUNTERS
]

feebas_fishing: Sequence[str] = [
    # TEMPLATE: MT_CORONET_B1F_ELUSIVE_FISHING_ENCOUNTERS
]

odd_keystone: Sequence[str] = [
    # TEMPLATE: ODD_KEYSTONE
]

roamers: Sequence[str] = [
    # TEMPLATE: ROAMERS
]

requiring_national_dex: Set[str] = {"roamers", "great_marsh_observatory_national_dex", "trophy_garden"}
