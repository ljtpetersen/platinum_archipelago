# data_gen_templates/event_checks.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping
from .locations import LocationCheck, VarCheck, FlagCheck, OnceCheck

event_checks: Mapping[str, LocationCheck] = {
    # TEMPLATE: EVENT_CHECKS
}
