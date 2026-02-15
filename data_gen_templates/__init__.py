# data_gen_templates/__init__.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping
from enum import StrEnum

class Hm(StrEnum):
    # TEMPLATE: HMS

    def badge_item(self) -> str | None:
        match self:
            # TEMPLATE: HM_BADGE_ITEMS
            case _: return None

    def tmhm_id(self) -> int:
        match self:
            # TEMPLATE: HM_TMHM_IDS
            case _: return 0 # TEMPLATE: DELETE

map_header_labels: Mapping[str, str] = {
    # TEMPLATE: MAP_HEADER_LABELS
}
