# data_gen_templates/charmap.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

charmap: dict[str, int] = {
    "←": 283,
    "↑": 284,
    "→": 285,
    "↓": 286,
    ",": 429,
    ".": 430,
    "'": 435,
    "-": 446,
    ":": 452,
    ";": 453,
    "!": 427,
    "?": 428,
    "\"": 437,
    "(": 441,
    ")": 442,
    "~": 451,
    "@": 464,
    "#": 448,
    "%": 466,
    "+": 445,
    "*": 447,
    "/": 433,
    "=": 449,
    " ": 478,
    "Œ": 415,
    "œ": 416,
    "Ş": 417,
    "ş": 418,
    "ª": 419,
    "º": 420,
    "ʳ": 423,
    "¡": 425,
    "¿": 426,
    "…": 431,
    "‘": 434,
    "’": 435,
    "“": 436,
    "”": 437,
    "„": 438,
    "«": 439,
    "»": 440,
    "♂": 443,
    "♀": 444,
    "♠": 454,
    "♣": 455,
    "♥": 456,
    "♦": 457,
    "★": 458,
    "🞊": 459,
    "○": 460,
    "□": 461,
    "△": 462,
    "♢": 463,
    "♪": 465,
    "☂": 469,
    "☺": 471,
    "ᵉ": 479,
    "°": 488,
    "_": 489,
}

def _init():
    A_val = 299
    charmap.update({chr(ord('A') + i):A_val + i for i in range(26)})
    a_val = 325
    charmap.update({chr(ord('a') + i):a_val + i for i in range(26)})
    zero_val = 289
    charmap.update({chr(ord('0') + i):zero_val + i for i in range(10)})
    A_grave_val = 351
    charmap.update({chr(ord('À') + i):A_grave_val + i for i in range(64)})

widths: list[int] = [
    7, 10, 10, 10, 10,  9, 10,  9, 10, 10, 10, 11, 11,  9, 11,  9,
    11, 10, 11,  9, 11, 10, 11,  9, 10, 11, 11, 10, 11, 10, 11, 11,
    11, 10, 11, 10, 10, 11, 10, 11,  9, 11, 10,  9, 10, 10, 10, 10,
    11, 11, 10, 11, 11, 10, 11, 11, 11, 11, 11, 10, 11, 11, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10,  9,  9, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 10, 11,  9,
    11, 10, 11,  9, 11, 10, 11, 10, 11, 10, 11, 10, 11,  9, 11,  9,
    11, 10, 11, 10, 10, 11, 10, 11,  9, 10, 10, 10, 10,  9,  9, 10,
    11, 11,  9, 10, 10, 10, 11, 11, 10, 11, 11, 10, 11, 11, 10,  9,
    10, 10, 10, 10, 10, 10, 10,  9, 10, 10,  9, 10,  9, 10, 10, 10,
    10,  7,  6,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
    7,  7,  7,  6,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,  7,
    7,  7,  7,  8,  7,  7,  7,  7,  7,  7,  6,  7,  7,  3,  6,  7,
    4,  7,  7,  7,  7,  7,  6,  7,  6,  7,  7,  7,  7,  6,  7,  0,
    6, 10,  5,  6,  9,  5,  8,  7,  7,  8,  8,  6,  6,  8,  8,  8,
    8,  8,  8,  8,  8,  5,  5,  5,  5,  8,  8,  8,  8,  8,  8,  8,
    8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,  8,
    8,  8, 11, 12, 11, 11, 11, 11, 11, 12,  7,  6,  6,  7,  6,  9,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  5,  6,  6,  3,  5,  6,  4,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6, 10,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6,  6,  6,  7,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6, 10,  6,  6,  6,  6,  6,  4,  4,  4,  4,  6,  6,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6, 10, 10,
    6,  6,  6,  6,  8,  8,  5,  7,  4,  6,  6,  6,  5,  5,  6,  6,
    6,  5,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  5,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,
    6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  4,  5, 12,
    12,  6,  1,  2,  4,  8, 16,  5,  6,  8,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

def encode_string(val: str, unknown_filler: str | None = None, max_len: int | None = None) -> bytes | None:
    out_len = 0
    def map_char(char: str) -> bytes:
        nonlocal out_len
        if char in charmap:
            id = charmap[char]
        elif unknown_filler is not None and unknown_filler in charmap:
            id = charmap[unknown_filler]
        else:
            raise ValueError(f"{char} not in charmap")
        out_len += widths[id - 1]
        if max_len is not None and out_len > max_len:
            return b''
        else:
            return int.to_bytes(id, 2, 'little')
    try:
        out_bytes = b''.join(map_char(char) for char in val)
    except ValueError:
        return None
    return out_bytes

_init()

def main():
    from sys import argv
    def compute_width(s: str) -> int:
        return sum(widths[charmap[c] - 1] for c in s)
    if len(argv) > 1:
        print("width of string is", compute_width(argv[-1]))
        print("note: maximum width of message is 212")

if __name__ == "__main__":
    main()
