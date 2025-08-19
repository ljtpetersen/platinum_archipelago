
from enum import StrEnum

class Hm(StrEnum):
    # TEMPLATE: HMS

    def badge_item(self) -> str | None:
        match self:
            # TEMPLATE: HM_BADGE_ITEMS
            case _: return None
