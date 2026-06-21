# client.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Iterable, Mapping, Set, Sequence
from dataclasses import dataclass
from enum import IntEnum
from itertools import batched, chain
from NetUtils import ClientStatus, NetworkItem
from Options import Toggle
from struct import unpack_from
import time
from typing import Any, Optional, TYPE_CHECKING, Tuple

import Utils

from .apnds import rom as ndsrom

from .data.locations import FlagCheck, LocationCheck, LocationTable, locations, VarCheck, OnceCheck, maximal_required_locations
from .data.trainers import trainers, trainer_id_to_trainer_const_name, TrainerCheck
from .data.species import regional_mons, species_id_to_const_name
from .data.event_checks import event_checks
from .items import get_item_classification
from .locations import raw_id_to_const_name
from .options import Goal, RemoteItems

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

AP_STRUCT_PTR_ADDRESS = 0x023DFFFC
AP_SUPPORTED_VERSIONS = {1}
AP_MAGIC = b' AP '

TRACKED_EVENTS = [
    "fen_badge",
    "met_oak_pal_park",
    "lake_verity_defeat_mars",
    "lake_explosion",
    "forest_badge",
    "cobble_badge",
    "galactic_hq_defeat_cyrus",
    "lake_valor_defeat_saturn",
    "lake_acuity_meet_jupiter",
    "icicle_badge",
    "eterna_defeat_team_galactic",
    "relic_badge",
    "coal_badge",
    "beacon_badge",
    "mine_badge",
    "beat_cynthia",
    "distortion_world",
    "valley_windworks_defeat_team_galactic",
    "stark_mountain_arrest_team_galactic",
    "activate_roaming_moltres_zapdos_articuno",
    "activate_roaming_cresselia",
    "activate_roaming_mesprit",
]
TRACKED_UNRANDOMIZED_REQUIRED_LOCATIONS = sorted(maximal_required_locations)
TRACKED_HEIGHT_MAP_HEADERS = {35, 350}

class CheatBits(IntEnum):
    UNLOCK_ALL_FLY_REGIONS = 1

@dataclass(frozen=True)
class VersionData:
    savedata_ptr_offset: int
    champion_flag: int
    vars_flags_offset_in_save: int
    vars_offset_in_vars_flags: int
    vars_flags_size: int
    flags_offset_in_vars_flags: int
    ap_save_offset: int
    recv_item_count_offset_in_ap_save: int
    once_loc_flags_offset_in_ap_save: int
    once_loc_flags_count: int
    deathlink_tx_offset: int
    num_blacked_out_offset_in_ap_save: int
    cheat_offset: int
    pokedex_offset_in_save: int
    pokedex_size: int
    trainersanity_flags_offset_in_ap_save: int
    trainersanity_flags_count: int
    player_pos_offset: int
    recv_state_offset: int
    remote_item_queue_offset: int
    remote_item_queue_size: int
    remote_item_queue_flags_offset_in_queue: int

AP_VERSION_DATA: Mapping[int, VersionData] = {
    1: VersionData(
        savedata_ptr_offset=16,
        champion_flag=2404,
        vars_flags_offset_in_save=0xDC0,
        vars_offset_in_vars_flags=0,
        vars_flags_size=0x3E0,
        flags_offset_in_vars_flags=0x240,
        ap_save_offset=0xCF60,
        recv_item_count_offset_in_ap_save=0,
        once_loc_flags_offset_in_ap_save=4,
        once_loc_flags_count=16,
        deathlink_tx_offset=21,
        num_blacked_out_offset_in_ap_save=8,
        cheat_offset=24,
        pokedex_offset_in_save=0x1370,
        pokedex_size=804,
        trainersanity_flags_offset_in_ap_save=12,
        trainersanity_flags_count=927,
        player_pos_offset=28,
        recv_state_offset=20,
        remote_item_queue_offset=44,
        remote_item_queue_size=64,
        remote_item_queue_flags_offset_in_queue=136,
    ),
}

@dataclass(frozen=True)
class VarsFlags:
    flags: bytes
    vars: bytes
    once_loc_flags: bytes
    trainersanity_flags: bytes

    def is_checked(self, check: LocationCheck) -> bool:
        if isinstance(check, FlagCheck):
            return self.get_flag(check.id) ^ check.invert
        elif isinstance(check, VarCheck):
            var = self.get_var(check.id)
            if var is not None:
                return check.op(var, check.value)
            else:
                return False
        elif isinstance(check, OnceCheck):
            return self.get_once_flag(check.id) ^ check.invert
        elif isinstance(check, TrainerCheck):
            return self.get_trainersanity_flag(check.id)
        else:
            return False

    def get_trainersanity_flag(self, flag_id: int) -> bool:
        if flag_id // 8 < len(self.trainersanity_flags):
            return self.trainersanity_flags[flag_id // 8] & (1 << (flag_id & 7)) != 0
        else:
            return False

    def get_once_flag(self, flag_id: int) -> bool:
        if flag_id // 8 < len(self.once_loc_flags):
            return self.once_loc_flags[flag_id // 8] & (1 << (flag_id & 7)) != 0
        else:
            return False

    def get_flag(self, flag_id: int) -> bool:
        if flag_id > 0 and flag_id // 8 < len(self.flags):
            return self.flags[flag_id // 8] & (1 << (flag_id & 7)) != 0
        else:
            return False

    def get_var(self, var_id: int) -> int | None:
        if var_id - 0x4000 < len(self.vars) // 2:
            var_id -= 0x4000
            return int.from_bytes(self.vars[2 * var_id:2 * (var_id + 1)], byteorder='little')

@dataclass(frozen=True)
class Pokedex:
    data: bytes

    def has_caught_dexsanity(self, id: int, req: bool) -> bool:
        if req:
            if not self.has_regular():
                return False
            if not self.has_national() and species_id_to_const_name[id] not in regional_mons:
                return False
        return self.has_caught(id)

    def has_caught(self, id: int):
        id -= 1
        return (self.data[4 + (id >> 3)] & (1 << (id & 7))) != 0

    def has_seen(self, id: int):
        id -= 1
        return (self.data[68 + (id >> 3)] & (1 << (id & 7))) != 0

    def has_regular(self) -> bool:
        return self.data[794] != 0

    def has_national(self) -> bool:
        return self.data[795] != 0

def dex_bytearray_to_seq(data: bytearray | bytes) -> Sequence[int]:
    return [v
        for v in range(1, 494)
        if (data[(v - 1) >> 3] & (1 << ((v - 1) & 7))) != 0
    ]

def seq_int_bytes(data: Iterable[int], len_per: int) -> bytes:
    return b''.join(v.to_bytes(len_per, 'little') for v in data)

def pack_nibbles(data: Iterable[int]) -> bytes:
    return b''.join((v0 & 0xF | v1 << 4 & 0xF0).to_bytes(1, 'little') for v0, v1 in batched(data, n=2))

@dataclass(frozen=True)
class RemoteItemQueue:
    size: int
    front: int
    back: int

    @staticmethod
    def from_bytes(size: int, data: bytes) -> "RemoteItemQueue":
        return RemoteItemQueue(size, *unpack_from("<2I", data))

    def amount_in_queue(self) -> int:
        if self.front >= self.back:
            return self.front - self.back
        else:
            return self.size + self.front - self.back

    def remaining_capacity(self) -> int:
        return self.size - self.amount_in_queue() - 1

    def get_writes(self, queue_addr: int, new_values: Sequence[NetworkItem], present_queue_flags: bytes, player: int) -> Sequence[Tuple[int, bytes, str]]:
        def item_flags(item: NetworkItem) -> int:
            if item.location <= 0:
                return get_item_classification(item.item).as_flag() | 8
            elif item.player == player:
                return 0
            else:
                return item.flags | 8

        new_front = (self.front + len(new_values)) & (self.size - 1)
        ret = [(queue_addr, new_front.to_bytes(4, 'little'), "ARM9 System Bus")]
        if new_front < self.front:
            first_upper = self.size - self.front
            if first_upper < len(new_values):
                ret.append((queue_addr + 8, seq_int_bytes((v.item for v in new_values[first_upper:]), 2), "ARM9 System Bus"))
                if len(new_values) - first_upper & 1 == 0:
                    ret.append((queue_addr + 8 + self.size * 2, pack_nibbles(item_flags(v) for v in new_values[first_upper:]), "ARM9 System Bus"))
                else:
                    ret.append((queue_addr + 8 + self.size * 2, pack_nibbles(chain((item_flags(v) for v in new_values[first_upper:]), [present_queue_flags[(len(new_values) - first_upper) // 2] >> 4])), "ARM9 System Bus"))
        else:
            first_upper = new_front - self.front
        if first_upper > 0:
            ret.append((queue_addr + 8 + self.front * 2, seq_int_bytes((v.item for v in new_values[:first_upper]), 2), "ARM9 System Bus"))
            item_flag_seq = []
            if self.front & 1 != 0:
                item_flag_seq.append(present_queue_flags[self.front // 2])
            item_flag_seq.extend(item_flags(v) for v in new_values[:first_upper])
            if self.front + first_upper & 1 != 0:
                item_flag_seq.append(present_queue_flags[(self.front + first_upper) // 2] >> 4)
            ret.append((queue_addr + 8 + self.size * 2 + self.front // 2, pack_nibbles(item_flag_seq), "ARM9 System Bus"))
        return ret

class PokemonPlatinumClient(BizHawkClient):
    game = "Pokemon Platinum"
    system = "NDS"
    patch_suffix = ".applatinum"
    ap_struct_address: int = 0
    rom_version: int = 0
    goal_check: LocationCheck | None
    local_checked_locations: Set[int]
    expected_header: bytes

    death_counter: Optional[int]
    previous_death_link: float
    ignore_next_death_link: bool

    cheat_bits: int
    added_cheat_command: bool

    current_map: int
    current_x: int
    current_y: int
    current_z: int
    local_tracked_events: int
    local_tracked_unrandomized_prog_locs: int
    local_seen_pokemon: bytearray
    local_caught_pokemon: bytearray
    notify_setup_complete: bool

    player_name: str | None

    death_link_group: str
    death_link_state: bool
    loaded_death_link: bool

    def __init__(self):
        super().__init__()

        self.player_name = None

    def initialize_client(self):
        self.goal_flag = None
        self.local_checked_locations = set()
        self.expected_header = AP_MAGIC * 3 + self.rom_version.to_bytes(length=4, byteorder='little')
        self.death_counter = None
        self.previous_death_link = 0
        self.ignore_next_death_link = False
        self.cheat_bits = 0
        self.added_cheat_command = False

        self.current_map = 0
        self.current_x = -1
        self.current_z = -1
        self.local_tracked_events = 0
        self.local_tracked_unrandomized_prog_locs = 0
        self.local_seen_pokemon = bytearray(64)
        self.local_caught_pokemon = bytearray(64)
        self.notify_setup_complete = False

        self.loaded_death_link = False
        self.death_link_group = ""
        self.death_link_state = False

    async def get_slot_name_and_remote_items(self, ctx: "BizHawkClientContext") -> Tuple[str | None, bool]:
        remote_items: bool = False
        try:
            header = ndsrom.Header((await bizhawk.read(ctx.bizhawk_ctx, [(0, 0x4000, "ROM")]))[0])
            fatb_offset = header.get_le(ndsrom.HeaderField.FATB_ROMOFFSET)
            fatb_size = header.get_le(ndsrom.HeaderField.FATB_BSIZE)
            fatb = (await bizhawk.read(ctx.bizhawk_ctx, [(fatb_offset, fatb_size, "ROM")]))[0]
            fntb_offset = header.get_le(ndsrom.HeaderField.FNTB_ROMOFFSET)
            fntb_size = header.get_le(ndsrom.HeaderField.FNTB_BSIZE)
            fntb = (await bizhawk.read(ctx.bizhawk_ctx, [(fntb_offset, fntb_size, "ROM")]))[0]
            filename_id_map = ndsrom.get_filename_id_map(fntb)
            ap_bin_id = filename_id_map["/ap.bin"]
            ap_bin_start, = unpack_from("<I", fatb, ap_bin_id * 8)
            ap_bin_bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(ap_bin_start, 97, "ROM")]))[0]
            name_end = ap_bin_bytes[:64].find(b'\0')
            remote_items = ap_bin_bytes[96] != 0
            if name_end != -1:
                player_name = ap_bin_bytes[:name_end].decode()
            else:
                player_name = ap_bin_bytes[:64].decode()

            return (player_name, remote_items)
        except UnicodeDecodeError:
            return (None, remote_items)
        except bizhawk.RequestFailedError:
            return (None, remote_items)

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        from CommonClient import logger
        def remove_commands():
            for command in ["cheat", "death_link_state", "death_link_group"]:
                if command in ctx.command_processor.commands:
                    del ctx.command_processor.commands[command]

        try:
            rom_name_bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(0, 12, "ROM")]))[0]
            rom_name = bytes([byte for byte in rom_name_bytes if byte != 0]).decode("ascii")
            if rom_name == "POKEMON PL":
                logger.info("ERROR: You appear to be running an unpatched version of Pokémon Platinum. "
                            "You need to generate a patch file and use it to create a patched ROM.")
                remove_commands()
                return False
            elif rom_name.startswith("PLAP "):
                bad = True
                try:
                    version = int(rom_name[5:].strip(), 16)
                    if version in AP_SUPPORTED_VERSIONS:
                        self.rom_version = version
                        bad = False
                except ValueError:
                    pass
                if bad:
                    logger.info("ERROR: The patch file used to create this ROM is not compatible with "
                                "this client. Double-check your client version against the version being "
                                "by the generator.")
                    remove_commands()
                    return False
            else:
                remove_commands()
                return False
        except UnicodeDecodeError:
            remove_commands()
            return False
        except bizhawk.RequestFailedError:
            remove_commands()
            return False

        self.player_name, remote_items = await self.get_slot_name_and_remote_items(ctx)
        ctx.game = self.game
        if remote_items:
            ctx.items_handling = 0b011
        else:
            ctx.items_handling = 0b001
        self.want_slot_data = True
        self.watcher_timeout = 0.125

        self.initialize_client()

        return True

    async def get_struct_addr(self, ctx: "BizHawkClientContext") -> None:
        try:
            addr = int.from_bytes((await bizhawk.read(ctx.bizhawk_ctx, [(AP_STRUCT_PTR_ADDRESS, 4, "ARM9 System Bus")]))[0], byteorder='little')
            if 0x2000000 < addr and addr < AP_STRUCT_PTR_ADDRESS:
                header = (await bizhawk.read(ctx.bizhawk_ctx, [(addr, 16, "ARM9 System Bus")]))[0]
                if header == self.expected_header:
                    self.ap_struct_address = addr
                    print(f"found ap struct at addr {addr:X}")
        except bizhawk.RequestFailedError:
            pass

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if ctx.server is None or ctx.server.socket.closed or ctx.slot_data is None:
            return

        version_data = AP_VERSION_DATA[self.rom_version]

        if self.ap_struct_address == 0:
            await self.get_struct_addr(ctx)
            return

        if ctx.slot_data["cheats_enabled"] == 1 and not self.added_cheat_command:
            self.added_cheat_command = True
            ctx.command_processor.commands["cheat"] = cmd_cheat

        if ctx.slot_data["goal"] == Goal.option_champion:
            self.goal_flag = event_checks["beat_cynthia"]

        if "remote_items" in ctx.slot_data and ctx.slot_data["remote_items"] != RemoteItems.option_off and not ctx.items_handling & 0b010: # type: ignore
            ctx.items_handling = 0b011
            Utils.async_start(ctx.send_msgs([{
                "cmd": "ConnectUpdate",
                "items_handling": ctx.items_handling
            }]))

        if not self.loaded_death_link:
            self.loaded_death_link = True
            if ctx.slot_data.get("death_link", Toggle.option_false) != Toggle.option_true:
                self.death_link_group = ""
                self.death_link_state = False
            else:
                self.death_link_group = ctx.slot_data.get("death_link_group", "")
                self.death_link_state = True
            ctx.command_processor.commands["death_link_state"] = cmd_death_link_state
            ctx.command_processor.commands["death_link_group"] = cmd_death_link_group

        try:
            ap_struct_guard = (self.ap_struct_address, self.expected_header, "ARM9 System Bus")
            guards: Mapping[str, Tuple[int, bytes, str]] = {}
            guards["AP STRUCT VALID"] = ap_struct_guard

            actual_header = (await bizhawk.read(ctx.bizhawk_ctx, [(ap_struct_guard[0], 16, "ARM9 System Bus")]))[0]
            if actual_header != self.expected_header:
                self.ap_struct_address = 0
                return

            if self.cheat_bits != 0:
                await self.handle_cheats(ctx, guards, version_data)

            read_result = await bizhawk.guarded_read(
                ctx.bizhawk_ctx,
                [
                    (self.ap_struct_address + version_data.savedata_ptr_offset, 4, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"]]
            )

            if read_result is None:
                return

            guards["SAVEDATA PTR"] = (self.ap_struct_address + version_data.savedata_ptr_offset, read_result[0], "ARM9 System Bus")

            await self.handle_death_link(ctx, guards, version_data)

            savedata_ptr = int.from_bytes(guards["SAVEDATA PTR"][1], byteorder='little')

            read_result = await bizhawk.guarded_read(
                ctx.bizhawk_ctx,
                [
                    (savedata_ptr + version_data.ap_save_offset + version_data.recv_item_count_offset_in_ap_save, 4, "ARM9 System Bus"),
                    (self.ap_struct_address + version_data.recv_state_offset, 1, "ARM9 System Bus"),
                    (self.ap_struct_address + version_data.remote_item_queue_offset, 8, "ARM9 System Bus"),
                    (self.ap_struct_address + version_data.remote_item_queue_offset + version_data.remote_item_queue_flags_offset_in_queue, version_data.remote_item_queue_size // 2, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"], guards["SAVEDATA PTR"]]
            )

            if read_result is None:
                return

            recv_item_count = int.from_bytes(read_result[0], byteorder='little')
            recv_state = read_result[1][0]
            remote_item_queue = RemoteItemQueue.from_bytes(version_data.remote_item_queue_size, read_result[2])
            amount_in_queue = remote_item_queue.amount_in_queue()
            if recv_state == 1 \
                and recv_item_count + amount_in_queue < len(ctx.items_received) \
                and remote_item_queue.remaining_capacity() > 0:
                start_idx = recv_item_count + amount_in_queue
                await bizhawk.guarded_write(
                    ctx.bizhawk_ctx,
                    remote_item_queue.get_writes(
                        self.ap_struct_address + version_data.remote_item_queue_offset,
                        [v for v in ctx.items_received[start_idx:start_idx + remote_item_queue.remaining_capacity()]],
                        read_result[3],
                        ctx.slot),
                    [
                        guards["AP STRUCT VALID"],
                        guards["SAVEDATA PTR"],
                    ]
                )

            read_result = await bizhawk.guarded_read(
                ctx.bizhawk_ctx,
                [
                    (savedata_ptr + version_data.vars_flags_offset_in_save, version_data.vars_flags_size, "ARM9 System Bus"),
                    (savedata_ptr + version_data.ap_save_offset + version_data.once_loc_flags_offset_in_ap_save, (version_data.once_loc_flags_count + 7) // 8, "ARM9 System Bus"),
                    (savedata_ptr + version_data.pokedex_offset_in_save, version_data.pokedex_size, "ARM9 System Bus"),
                    (savedata_ptr + version_data.ap_save_offset + version_data.trainersanity_flags_offset_in_ap_save, (version_data.trainersanity_flags_count + 7) // 8, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"], guards["SAVEDATA PTR"]],
            )
            if read_result is None:
                return
            vars_flags_bytes = read_result[0]
            vars_bytes = vars_flags_bytes[version_data.vars_offset_in_vars_flags:version_data.flags_offset_in_vars_flags]
            flags_bytes = vars_flags_bytes[version_data.flags_offset_in_vars_flags:]

            vars_flags = VarsFlags(flags=flags_bytes, vars=vars_bytes, once_loc_flags=read_result[1], trainersanity_flags=read_result[3])
            pokedex = Pokedex(data=read_result[2])

            local_checked_locations = set()
            game_clear = vars_flags.is_checked(self.goal_flag) # type: ignore
            local_tracked_events = 0
            local_tracked_unrandomized_prog_locs = 0
            local_seen_pokemon = bytearray(64)
            local_caught_pokemon = bytearray(64)

            for k in ctx.missing_locations:
                if k >> 16 == LocationTable.DEX:
                    if pokedex.has_caught_dexsanity(k & 0xFFFF, ctx.slot_data["dexsanity_mode"] >= 2):
                        local_checked_locations.add(k)
                elif k >> 16 == LocationTable.TRAINERS:
                    trainer = trainers[trainer_id_to_trainer_const_name[k & 0xFFFF]]
                    if vars_flags.is_checked(trainer.get_check()):
                        local_checked_locations.add(k)
                else:
                    loc = locations[raw_id_to_const_name[k]]
                    if vars_flags.is_checked(loc.check):
                        local_checked_locations.add(k)

            for k, event in enumerate(TRACKED_EVENTS):
                if vars_flags.is_checked(event_checks[event]):
                    local_tracked_events |= 1 << k

            for k, loc in enumerate(TRACKED_UNRANDOMIZED_REQUIRED_LOCATIONS):
                if vars_flags.is_checked(locations[loc].check):
                    local_tracked_unrandomized_prog_locs |= 1 << k

            for i in range(0, 493):
                if pokedex.has_seen(i + 1):
                    local_seen_pokemon[i >> 3] |= 1 << (i & 7)
                if pokedex.has_caught(i + 1):
                    local_caught_pokemon[i >> 3] |= 1 << (i & 7)

            if local_checked_locations != self.local_checked_locations:
                await ctx.check_locations(local_checked_locations)

                self.local_checked_locations = local_checked_locations


            packages = []

            if local_seen_pokemon != self.local_seen_pokemon:
                seq = dex_bytearray_to_seq(local_seen_pokemon)
                packages.append({
                    "cmd": "Set",
                    "key": f"pokemon_platinum_seen_pokemon_{ctx.team}_{ctx.slot}",
                    "default": [],
                    "want_reply": False,
                    "operations": [{"operation": "replace", "value": seq}]
                })

            if local_caught_pokemon != self.local_caught_pokemon:
                seq = dex_bytearray_to_seq(local_caught_pokemon)
                packages.append({
                    "cmd": "Set",
                    "key": f"pokemon_platinum_caught_pokemon_{ctx.team}_{ctx.slot}",
                    "default": [],
                    "want_reply": False,
                    "operations": [{"operation": "replace", "value": seq}]
                })

            if packages:
                await ctx.send_msgs(packages)

                self.local_seen_pokemon = local_seen_pokemon
                self.local_caught_pokemon = local_caught_pokemon

            if local_tracked_events != self.local_tracked_events:
                await ctx.send_msgs([{
                    "cmd": "Set",
                    "key": f"pokemon_platinum_tracked_events_{ctx.team}_{ctx.slot}",
                    "default": 0,
                    "want_reply": False,
                    "operations": [{"operation": "or", "value": local_tracked_events}]
                }])
                self.local_tracked_events = local_tracked_events

            if local_tracked_unrandomized_prog_locs != self.local_tracked_unrandomized_prog_locs:
                for chunk in range((len(TRACKED_UNRANDOMIZED_REQUIRED_LOCATIONS) + 31) // 32):
                    await ctx.send_msgs([{
                        "cmd": "Set",
                        "key": f"pokemon_platinum_tracked_unrandomized_required_locations_{ctx.team}_{ctx.slot}_{chunk}",
                        "default": 0,
                        "want_reply": False,
                        "operations": [{"operation": "or", "value": (local_tracked_unrandomized_prog_locs >> (chunk * 32)) & 0xFFFFFFFF}]
                    }])
                self.local_tracked_unrandomized_prog_locs = local_tracked_unrandomized_prog_locs


            if not ctx.finished_game and game_clear:
                ctx.finished_game = True
                await ctx.send_msgs([{
                    "cmd": "StatusUpdate",
                    "status": ClientStatus.CLIENT_GOAL,
                }])

            read_result = await bizhawk.guarded_read(
                ctx.bizhawk_ctx,
                [
                    (self.ap_struct_address + version_data.player_pos_offset, 16, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"]]
            )

            if read_result is None:
                return

            current_x, current_y, current_z, current_map, pos_lock = unpack_from("<3IHB", read_result[0])
            if current_map not in TRACKED_HEIGHT_MAP_HEADERS:
                current_y = 0
            if pos_lock == 0 and (current_map != self.current_map or current_x != self.current_x or current_y != self.current_y or current_z != self.current_z):
                self.current_map = current_map
                self.current_x = current_x
                self.current_y = current_y
                self.current_z = current_z
                message = [{"cmd": "Bounce", "slots": [ctx.slot],
                           "data": {
                               "mapNumber": current_map,
                               "matrixX": current_x,
                               "matrixZ": current_z,
                               "playerY": current_y,
                           }}]
                await ctx.send_msgs(message)

        except bizhawk.RequestFailedError:
            pass

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict[str, Any]) -> None:
        super().on_package(ctx, cmd, args)
        
        from CommonClient import logger

        if cmd == "Bounced":
            tags = args.get("tags", [])
            if "DeathLink" + self.death_link_group in tags and ctx.last_death_link != args["data"]["time"]:
                ctx.last_death_link = max(args["data"]["time"], ctx.last_death_link)
                text = args["data"].get("cause", "")
                if text:
                    logger.info("DeathLink: " + text)
                else:
                    logger.info("DeathLink: Received from " + args["data"]["source"])

    async def handle_death_link(self, ctx: "BizHawkClientContext", guards: Mapping[str, Tuple[int, bytes, str]], version_data: VersionData) -> None:
        if not self.death_link_state:
            old_tags = ctx.tags.copy()
            ctx.tags = {t for t in ctx.tags if not t.startswith("DeathLink")}
            if old_tags != ctx.tags and ctx.server and not ctx.server.socket.closed:
                await ctx.send_msgs([{"cmd": "ConnectUpdate", "tags": ctx.tags}])
            return

        if "DeathLink" + self.death_link_group not in ctx.tags:
            old_tags = ctx.tags.copy()
            ctx.tags = {t for t in ctx.tags if not t.startswith("DeathLink")}
            ctx.tags.add("DeathLink" + self.death_link_group)
            if old_tags != ctx.tags and ctx.server and not ctx.server.socket.closed:
                await ctx.send_msgs([{"cmd": "ConnectUpdate", "tags": ctx.tags}])
            self.previous_death_link = ctx.last_death_link

        if self.previous_death_link != ctx.last_death_link:
            self.previous_death_link = ctx.last_death_link
            if self.ignore_next_death_link:
                self.ignore_next_death_link = False
            else:
                if await bizhawk.guarded_write(
                    ctx.bizhawk_ctx,
                    [(self.ap_struct_address + version_data.deathlink_tx_offset, b'\x01', "ARM9 System Bus")],
                    [guards["AP STRUCT VALID"]],
                ):
                    return

        savedata_ptr = int.from_bytes(guards["SAVEDATA PTR"][1], byteorder='little')
        res = await bizhawk.guarded_read(
            ctx.bizhawk_ctx,
            [
                (savedata_ptr + version_data.ap_save_offset + version_data.num_blacked_out_offset_in_ap_save, 4, "ARM9 System Bus"),
            ],
            [guards["AP STRUCT VALID"], guards["SAVEDATA PTR"]]
        )
        if res is None:
            return

        num_blacked_out = int.from_bytes(res[0], 'little')
        if self.death_counter is None:
            self.death_counter = num_blacked_out
        elif num_blacked_out > self.death_counter:
            if ctx.server and ctx.server.socket:
                from CommonClient import logger
                logger.info("DeathLink: Sending death to your friends...")
                ctx.last_death_link = time.time()
                await ctx.send_msgs([{
                    "cmd": "Bounce",
                    "tags": ["DeathLink" + self.death_link_group],
                    "data": {
                        "time": ctx.last_death_link,
                        "source": ctx.player_names[ctx.slot],
                        "cause": f"{ctx.player_names[ctx.slot]} is out of usable POKéMON! " # type: ignore
                                 f"{ctx.player_names[ctx.slot]} blacked out!", # type: ignore
                    },
                }])
            self.ignore_next_death_link = True
            self.death_counter = num_blacked_out

    async def handle_cheats(self, ctx: "BizHawkClientContext", guards: Mapping[str, Tuple[int, bytes, str]], version_data: VersionData) -> None:
        read_result = await bizhawk.guarded_read(
            ctx.bizhawk_ctx,
            [(self.ap_struct_address + version_data.cheat_offset, 4, "ARM9 System Bus")],
            [guards["AP STRUCT VALID"]]
        )

        if read_result is None:
            return

        old_bits = int.from_bytes(read_result[0], 'little')
        if (old_bits | self.cheat_bits) == old_bits:
            self.cheat_bits = 0
            return
        old_bits |= self.cheat_bits
        self.cheat_bits = 0

        await bizhawk.guarded_write(
            ctx.bizhawk_ctx,
            [(self.ap_struct_address + version_data.cheat_offset, old_bits.to_bytes(4, 'little'), "ARM9 System Bus")],
            [guards["AP STRUCT VALID"]]
        )

    async def set_auth(self, ctx: "BizHawkClientContext") -> None:
        if self.player_name is not None:
            ctx.auth = self.player_name

def cmd_cheat(self: "BizHawkClientCommandProcessor", name: str | None = None) -> None:
    """Activate a Pokémon Platinum Cheat. Enter the command without any arguments to list all cheats."""
    from CommonClient import logger

    handler: PokemonPlatinumClient = self.ctx.client_handler # type: ignore
    assert isinstance(handler, PokemonPlatinumClient)
    if name is None:
        logger.info("Possible Pokémon Platinum cheats: " + " ".join(CheatBits._member_names_))
    elif name in CheatBits._member_map_:
        handler.cheat_bits |= getattr(CheatBits, name)
        logger.info("Activating Pokémon Platinum Cheat " + name)
    else:
        logger.error("Unknown Pokémon Platinum cheat: " + name)

def cmd_death_link_state(self: "BizHawkClientCommandProcessor", state: str | None = None) -> None:
    """Change the death link state. Enter the command without any arguments to print the current state. States are on or off."""
    from CommonClient import logger

    handler: PokemonPlatinumClient = self.ctx.client_handler # type: ignore
    assert isinstance(handler, PokemonPlatinumClient)
    if state is None:
        logger.info("Current death link state: " + ("on" if handler.death_link_state else "off"))
    elif state.lower() == "on":
        handler.death_link_state = True
        logger.info("Death link state set to on")
    elif state.lower() == "off":
        handler.death_link_state = False
        logger.info("Death link state set to off")

def cmd_death_link_group(self: "BizHawkClientCommandProcessor", group: str | None = None) -> None:
    """Change the death link group. Enter the comand without any arguments to print the current group. Use "" as the argument for the default group."""
    from CommonClient import logger

    handler: PokemonPlatinumClient = self.ctx.client_handler # type: ignore
    assert isinstance(handler, PokemonPlatinumClient)
    if group is None:
        logger.info(f"Current death link group: \"{handler.death_link_group}\"")
    else:
        handler.death_link_group = group
        logger.info(f"Set death link group to \"{group}\"")
