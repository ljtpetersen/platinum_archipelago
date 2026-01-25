# client.py
#
# Copyright (C) 2025 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, Set
from dataclasses import dataclass
from enum import IntEnum
from NetUtils import ClientStatus
from Options import Toggle
from typing import Optional, TYPE_CHECKING, Tuple

import Utils

from .data.locations import FlagCheck, LocationCheck, locations, VarCheck, OnceCheck
from .locations import raw_id_to_const_name
from .options import Goal, RemoteItems

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

AP_STRUCT_PTR_ADDRESS = 0x023DFFFC
AP_SUPPORTED_VERSIONS = {1}
AP_MAGIC = b' AP '

class CheatBits(IntEnum):
    UNLOCK_ALL_FLY_REGIONS = 1

@dataclass(frozen=True)
class VersionData:
    savedata_ptr_offset: int
    champion_flag: int
    recv_item_id_offset: int
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

AP_VERSION_DATA: Mapping[int, VersionData] = {
    1: VersionData(
        savedata_ptr_offset=16,
        champion_flag=2404,
        recv_item_id_offset=20,
        vars_flags_offset_in_save=0xDC0,
        vars_offset_in_vars_flags=0,
        vars_flags_size=0x3E0,
        flags_offset_in_vars_flags=0x240,
        ap_save_offset=0xCF60,
        recv_item_count_offset_in_ap_save=0,
        once_loc_flags_offset_in_ap_save=8,
        once_loc_flags_count=16,
        deathlink_tx_offset=22,
        num_blacked_out_offset_in_ap_save=12,
        cheat_offset=24,
    ),
}

@dataclass(frozen=True)
class VarsFlags:
    flags: bytes
    vars: bytes
    once_loc_flags: bytes

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

class PokemonPlatinumClient(BizHawkClient):
    game = "Pokemon Platinum"
    system = "NDS"
    patch_suffix = ".applatinum"
    ap_struct_address: int = 0
    rom_version: int = 0
    goal_flag: FlagCheck | None
    local_checked_locations: Set[int]
    expected_header: bytes

    death_counter: Optional[int]
    previous_death_link: float
    ignore_next_death_link: bool

    cheat_bits: int
    added_cheat_command: bool

    def initialize_client(self):
        self.goal_flag = None
        self.local_checked_locations = set()
        self.expected_header = AP_MAGIC * 3 + self.rom_version.to_bytes(length=4, byteorder='little')
        self.death_counter = None
        self.previous_death_link = 0
        self.ignore_next_death_link = False
        self.cheat_bits = 0
        self.added_cheat_command = False

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        from CommonClient import logger
        def remove_cheat():
            if "cheat" in ctx.command_processor.commands:
                del ctx.command_processor.commands["cheat"]

        try:
            rom_name_bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(0, 12, "ROM")]))[0]
            rom_name = bytes([byte for byte in rom_name_bytes if byte != 0]).decode("ascii")
            if rom_name == "POKEMON PL":
                logger.info("ERROR: You appear to be running an unpatched version of Pokémon Platinum. "
                            "You need to generate a patch file and use it to create a patched ROM.")
                remove_cheat()
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
                    remove_cheat()
                    return False
            else:
                remove_cheat()
                return False
        except UnicodeDecodeError:
            remove_cheat()
            return False
        except bizhawk.RequestFailedError:
            remove_cheat()
            return False

        ctx.game = self.game
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
            self.goal_flag = FlagCheck(id=version_data.champion_flag)

        if "remote_items" in ctx.slot_data and ctx.slot_data["remote_items"] == RemoteItems.option_true and not ctx.items_handling & 0b010: # type: ignore
            ctx.items_handling = 0b011
            Utils.async_start(ctx.send_msgs([{
                "cmd": "ConnectUpdate",
                "items_handling": ctx.items_handling
            }]))

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
                    (self.ap_struct_address + version_data.recv_item_id_offset, 2, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"], guards["SAVEDATA PTR"]]
            )

            if read_result is None:
                return

            recv_item_count = int.from_bytes(read_result[0], byteorder='little')
            recv_item_id = int.from_bytes(read_result[1], byteorder='little')
            if recv_item_id == 0xFFFF and recv_item_count < len(ctx.items_received):
                next_item = ctx.items_received[recv_item_count].item
                if await bizhawk.guarded_write(
                    ctx.bizhawk_ctx,
                    [
                        (self.ap_struct_address + version_data.recv_item_id_offset, next_item.to_bytes(length=2, byteorder='little'), "ARM9 System Bus"),
                    ],
                    [
                        guards["AP STRUCT VALID"],
                        guards["SAVEDATA PTR"],
                        (self.ap_struct_address + version_data.recv_item_id_offset, b'\xFF\xFF', "ARM9 System Bus"),
                    ]
                ):
                    return

            read_result = await bizhawk.guarded_read(
                ctx.bizhawk_ctx,
                [
                    (savedata_ptr + version_data.vars_flags_offset_in_save, version_data.vars_flags_size, "ARM9 System Bus"),
                    (savedata_ptr + version_data.ap_save_offset + version_data.once_loc_flags_offset_in_ap_save, version_data.once_loc_flags_count // 8, "ARM9 System Bus"),
                ],
                [guards["AP STRUCT VALID"], guards["SAVEDATA PTR"]],
            )
            if read_result is None:
                return
            vars_flags_bytes = read_result[0]
            vars_bytes = vars_flags_bytes[version_data.vars_offset_in_vars_flags:version_data.flags_offset_in_vars_flags]
            flags_bytes = vars_flags_bytes[version_data.flags_offset_in_vars_flags:]

            vars_flags = VarsFlags(flags=flags_bytes, vars=vars_bytes, once_loc_flags=read_result[1])

            local_checked_locations = set()
            game_clear = vars_flags.is_checked(self.goal_flag) # type: ignore

            for k, loc in map(lambda k : (k, locations[raw_id_to_const_name[k]]), ctx.missing_locations):
                if vars_flags.is_checked(loc.check):
                    local_checked_locations.add(k)

            if local_checked_locations != self.local_checked_locations:
                await ctx.check_locations(local_checked_locations)

                self.local_checked_locations = local_checked_locations

            if not ctx.finished_game and game_clear:
                ctx.finished_game = True
                await ctx.send_msgs([{
                    "cmd": "StatusUpdate",
                    "status": ClientStatus.CLIENT_GOAL,
                }])
        except bizhawk.RequestFailedError:
            pass

    async def handle_death_link(self, ctx: "BizHawkClientContext", guards: Mapping[str, Tuple[int, bytes, str]], version_data: VersionData) -> None:
        if ctx.slot_data.get("death_link", Toggle.option_false) != Toggle.option_true: # type: ignore
            return

        if "DeathLink" not in ctx.tags:
            await ctx.update_death_link(True)
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
            await ctx.send_death(f"{ctx.player_names[ctx.slot]} is out of usable POKéMON! " # type: ignore
                                 f"{ctx.player_names[ctx.slot]} blacked out!") # type: ignore
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
