# data_gen_templates/__init__.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from enum import StrEnum

class Hm(StrEnum):
    # TEMPLATE: HMS

    def badge_item(self) -> str | None:
        match self:
            # TEMPLATE: HM_BADGE_ITEMS
            case _: return None
