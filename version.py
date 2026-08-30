# version.py
#
# Copyright (C) 2026 James Petersen <m@jamespetersen.ca>

VERSION = "0.2.0"

def version_int(version: str) -> int:
    major, minor, rev = (int(s) for s in version.split('.'))
    return (major << 16) | (minor << 8) | rev

VERSION_INT = version_int(VERSION)
