import bsdiff4
import os
import pkgutil
import random
from typing import Any, Dict, TYPE_CHECKING
from settings import get_settings
from worlds.Files import APAutoPatchInterface
import zipfile

from .data.charmap import charmap
from .data.locations import locations, LocationTable
from .data.items import items

if TYPE_CHECKING:
    from . import PokemonPlatinumWorld

PLATINUM_1_0_US_HASH = "d66ad7a2a0068b5d46e0781ca4953ae9"
PLATINUM_1_1_US_HASH = "ab828b0d13f09469a71460a34d0de51b"

class PokemonPlatinumPatch(APAutoPatchInterface):
    game = "Pokemon Platinum"
    patch_file_ending = ".applatinum"
    hashes: list[str | bytes] = []
    source_data: bytes
    files: Dict[str, bytes]
    result_file_ending = ".nds"

    @staticmethod
    def get_source_data() -> bytes:
        with open(get_settings().pokemon_platinum_settings.rom_file, "rb") as infile:
            base_rom_bytes = bytes(infile.read())
        return base_rom_bytes

    @staticmethod
    def get_source_data_with_cache() -> bytes:
        if not hasattr(PokemonPlatinumPatch, "source_data"):
            PokemonPlatinumPatch.source_data = PokemonPlatinumPatch.get_source_data()
        return PokemonPlatinumPatch.source_data

    def patch(self, target: str) -> None:
        self.read()
        data = PokemonPlatinumPatch.get_source_data_with_cache()
        rom_version = data[0x01E]
        if rom_version == 0:
            patch_name = "base_patch_us_rev0.bsdiff4"
        else:
            patch_name = "base_patch_us_rev1.bsdiff4"
        data = bytearray(bsdiff4.patch(data, self.get_file(patch_name)))

        ap_bin_start = data.find(b'AP BIN FILLER ' * 5)
        ap_bin_end = data.find(b'\0', ap_bin_start)
        ap_bin_len = ap_bin_end - ap_bin_start + 1

        ap_bin = self.get_file("ap.bin")
        if len(ap_bin) > ap_bin_len:
            raise IndexError(f"ap.bin length is too long to fit in ROM. ap.bin: {len(ap_bin)}, capacity: {ap_bin_len}")
        data[ap_bin_start:ap_bin_start + len(ap_bin)] = ap_bin

        with open(target, 'wb') as f:
            f.write(data)

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.files = {}

    def get_manifest(self) -> Dict[str, Any]:
        manifest = super().get_manifest()
        manifest["result_file_ending"] = self.result_file_ending
        manifest["allowed_hashes"] = self.hashes
        return manifest

    def write_contents(self, opened_zipfile: zipfile.ZipFile) -> None:
        super().write_contents(opened_zipfile)
        for file in self.files:
            opened_zipfile.writestr(file, self.files[file],
                                    compress_type=zipfile.ZIP_STORED if file.endswith(".bsdiff4") else None)

    def get_file(self, file: str) -> bytes:
        if file not in self.files:
            self.read()
        return self.files[file]

    def write_file(self, file_name: str, file: bytes) -> None:
        self.files[file_name] = file

def encode_name(name: str) -> bytes | None:
    ret = bytes()
    state = "normal"
    buf = ""
    for c in name:
        match state:
            case "normal":
                if c == '\\':
                    state = "escape"
                elif c == '{':
                    state = "bracket"
                    buf = ""
                elif c in charmap:
                    ret += charmap[c].to_bytes(length=2, byteorder='little')
                else:
                    return None
            case "escape":
                if "\\" + c in charmap:
                    ret += charmap["\\" + c].to_bytes(length=2, byteorder='little')
                    state = "normal"
                else:
                    return None
            case "bracket":
                if c == '}':
                    if buf in charmap:
                        ret += charmap[buf].to_bytes(length=2, byteorder='little')
                    else:
                        return None
                    state = "normal"
                else:
                    buf += c
        if len(ret) >= 15:
            return None
    return ret + b'\xFF' * (16 - len(ret))

def process_name(name: str, world: "PokemonPlatinumWorld") -> bytes:
    if name == "vanilla":
        return b'\xFF' * 16
    if name == "random":
        other_players = [world.multiworld.get_file_safe_player_name(id) for id in world.multiworld.player_name if id != world.player] # type: ignore
        random.shuffle(other_players)
        # if no player name matches, then return vanilla
        for name in other_players:
            ret = encode_name(name)
            if ret:
                return ret
        return b'\xFF' * 16
    if name == "player_name":
        ret = encode_name(world.multiworld.get_file_safe_player_name(world.player))
    else:
        ret = encode_name(name)
    if ret:
        return ret
    else:
        return b'\xFF' * 16

def generate_output(world: "PokemonPlatinumWorld", output_directory: str, patch: PokemonPlatinumPatch) -> None:
    ap_bin = bytes()
    ap_bin += process_name(world.options.game_options["default_player_name"], world)
    ap_bin += process_name(world.options.game_options["default_rival_name"], world)
    match world.options.game_options["default_gender"]:
        case "male":
            ap_bin += b'\x00'
        case "female":
            ap_bin += b'\x01'
        case "random":
            ap_bin += random.choice([b'\x00', b'\x01'])
        case _:
            ap_bin += b'\x02'
    match world.options.game_options["text_speed"]:
        case "fast":
            ap_bin += b'\x02'
        case "slow":
            ap_bin += b'\x00'
        case _:
            ap_bin += b'\x01'
    match world.options.game_options["sound"]:
        case "mono":
            ap_bin += b'\x01'
        case _:
            ap_bin += b'\x00'
    match world.options.game_options["battle_scene"]:
        case "off":
            ap_bin += b'\x01'
        case _:
            ap_bin += b'\x00'
    match world.options.game_options["battle_style"]:
        case "set":
            ap_bin += b'\x01'
        case _:
            ap_bin += b'\x00'
    match world.options.game_options["button_mode"]:
        case "start=x":
            ap_bin += b'\x01'
        case "l=a":
            ap_bin += b'\x02'
        case _:
            ap_bin += b'\x00'
    text_frame = world.options.game_options["text_frame"]
    if isinstance(text_frame, int) and 1 <= text_frame and text_frame <= 20:
        ap_bin += (text_frame - 1).to_bytes(length=1, byteorder='little')
    else:
        ap_bin += b'\x00'
    match world.options.game_options["received_items_notification"]:
        case "nothing":
            ap_bin += b'\x00'
        case "message":
            ap_bin += b'\x03'
        case _:
            ap_bin += b'\x04'

    if world.options.hm_badge_requirement.value == 1:
        hm_accum = 0
        hm_order = ["CUT", "FLY", "SURF", "STRENGTH", "DEFOG", "ROCK_SMASH", "WATERFALL", "ROCK_CLIMB"]
        for i, v in enumerate(hm_order):
            if v in world.options.remove_badge_requirements:
                hm_accum |= 1 << i
    else:
        hm_accum = 0xFF
    ap_bin += hm_accum.to_bytes(length=1, byteorder='little')
    if len(ap_bin) % 2 == 1:
        ap_bin += b'\x00'

    tables: dict[LocationTable, bytearray] = {}

    def put_in_table(table: LocationTable, id: int, item_id: int):
        if table not in tables:
            tables[table] = bytearray()
        l = len(tables[table])
        if id >= l // 2:
            tables[table] = tables[table] + b'\x00\xF0' * (id - l // 2 + 1)
        tables[table][2*id:2*(id+1)] = item_id.to_bytes(length=2, byteorder='little')

    filled_locations = set()

    for location in world.multiworld.get_locations(world.player):
        if location.address is None or location.item is None or location.item.code is None:
            continue
        table = LocationTable(location.address >> 16)
        id = location.address & 0xFFFF
        filled_locations.add(location.name)
        if location.item.player == world.player:
            item_id = location.item.code
        else:
            item_id = 0xE000
        put_in_table(table, id, item_id)

    for location in locations.values():
        if location.label not in filled_locations:
            put_in_table(location.table, location.id, items[location.original_item].get_raw_id())

    ap_bin += len(tables).to_bytes(length=4, byteorder='little')
    for table in sorted(tables.keys()):
        data = tables[table]
        ap_bin += (len(data) // 2).to_bytes(length=4, byteorder='little')
        ap_bin += data

    patch.write_file("ap.bin", ap_bin)

    out_file_name = world.multiworld.get_out_file_name_base(world.player)
    patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))
