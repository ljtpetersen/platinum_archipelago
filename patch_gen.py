#!/usr/bin/env python3

# patch_gen.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE


from bsdiff4 import file_diff
from sys import argv

def main():
    file_diff(argv[1], argv[2], argv[3])

if __name__ == "__main__":
    main()
