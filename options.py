# options.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Mapping, MutableMapping, Sequence, Set
from dataclasses import dataclass
from typing import Any
from Options import Choice, DeathLink, DefaultOnToggle, NamedRange, OptionDict, OptionError, OptionSet, PerGameCommonOptions, Range, Toggle

from .data import special_encounters
from .data.species import species, regional_mons
from .data.regions import regions
from .data.trainers import trainer_party_supporting_starters, trainers, trainer_requires_national_dex
from .data.encounters import encounters, encounter_type_pairs, national_dex_requiring_encs

class SpeciesBlacklist(OptionSet):
    cached_blacklist: Set[str] | None = None

    def blacklist(self) -> Set[str]:
        if self.cached_blacklist is None:
            if "legendaries" in self:
                self.cached_blacklist = (frozenset(self.value) - {"legendaries"}) | set(regional_mons)
            else:
                self.cached_blacklist = frozenset(self.value)
        return self.cached_blacklist

class RandomizeHms(DefaultOnToggle):
    """Adds the HMs to the pool."""
    display_name = "Randomize HMs"

class RandomizeBadges(DefaultOnToggle):
    """Adds the badges to the pool."""
    display_name = "Randomize Badges"

class RandomizeOverworlds(DefaultOnToggle):
    """Adds overworld items to the pool."""
    display_name = "Randomize Overworlds"

class RandomizeHiddenItems(Toggle):
    """Adds hidden items to the pool."""
    display_name = "Randomize Hidden Items"

class RandomizeNpcGifts(DefaultOnToggle):
    """Adds NPC gifts to the pool."""
    display_name = "Randomize NPC Gifts"

class RandomizeKeyItems(Choice):
    """Adds key items to the pool."""
    display_name = "Randomize Key Items"
    default = 1
    option_vanilla = 0
    option_most = 1
    option_all = 2

    def are_most_randomized(self) -> bool:
        return self.value >= self.option_most

class RandomizeRods(DefaultOnToggle):
    """Adds rods to the pool."""
    display_name = "Randomize Rods"

class RandomizePoketchApps(DefaultOnToggle):
    """Adds Pokétch apps to the pool (and the Pokétch)."""
    display_name = "Randomize Poketch Apps"

class RandomizeRunningShoes(Toggle):
    """Adds the running shoes to the pool."""
    display_name = "Randomize Running Shoes"

class RandomizeBicycle(Toggle):
    """Adds the bicycle to the pool."""
    display_name = "Randomize Bicycle"

class RandomizePokedex(Toggle):
    """Add the Pokedex to the pool. Note: this also adds the national dex to the pool."""
    display_name = "Randomize Pokedex"

class RandomizeAccessories(Toggle):
    """Adds fashion accessories to the item pool."""
    display_name = "Randomize Accessories"

class RandomizeCartridges(Choice):
    """Adds the GBA cartridges to the item pool. The no location option removes the location and adds the cartridges to the starting inventory. The false option means they won't be randomized."""
    display_name = "Randomize Cartridges"
    default = 1
    option_true = 1
    option_false = 0
    option_no_location = 2

class RandomizeTimeItems(Choice):
    """Adds the time items to the item pool. The no location option removes the location and adds the time items to the starting inventory. The false option means they won't be randomized."""
    display_name = "Randomize Time Items"
    default = 1
    option_true = 1
    option_false = 0
    option_no_location = 2

class HmBadgeRequirements(DefaultOnToggle):
    """Require the corresponding badge to use an HM outside of battle."""
    display_name = "Require Badges for HMs"

class RemoveBadgeRequirement(OptionSet):
    """
    Specify which HMs do not require a badge to use outside of battle. This overrides the HM Badge Requirements setting.

    HMs should be provided in the form: "fly", "waterfall", "rock_smash", etc.
    """
    display_name = "Remove Badge Requirement"
    valid_keys = ["cut", "fly", "surf", "strength", "defog", "rock_smash", "waterfall", "rock_climb"]

class VisibilityHmLogic(DefaultOnToggle):
    """Logically require Flash or Defog for traversing and finding locations in applicable regions."""
    display_name = "Logically Require Flash or Defog for Applicable Regions"

class DowsingMachineLogic(DefaultOnToggle):
    """Logically require the Dowsing Machine to find hidden items."""
    display_name = "Logically Require Dowsing Machine for Hidden Items"

class Goal(Choice):
    """The goal of the randomizer. Currently, this only supports defeating the champion and entering the hall of fame."""
    display_name = "Goal"
    default = 0
    option_champion = 0

class AddMasterRepel(Toggle):
    """
    Add a master repel item to the item pool. The master repel is a key item.
    It is a repel that blocks all encounters, and never runs out.
    """
    display_name = "Add Master Repel"

class ExpMultiplier(Range):
    """Set an experience multiplier for all gained experience."""
    display_name = "Exp. Multiplier"
    range_start = 1
    range_end = 16
    default = 1

class BlindTrainers(Toggle):
    """
    Set whether trainers will be blind.

    This option can also be modified in the in-game options menu.
    """
    display_name = "Blind Trainers"

class GameOptions(OptionDict):
    """
    Presets in-game options.

    Allowed options and values, with default first:

    text_speed: mid/slow/fast - Sets the text speed
    sound: stereo/mono - Sets the shound mode
    battle_scene: on/off - Sets whether the battle animations are shown
    battle_style: shift/set - Sets whether pokemon can be changed when the opponent's pokemon faints
    button_mode: normal/start=x/l=a - Sets the button mode
    text_frame: 1-20 - Sets the textbox frame. "random" will pick a random frame.
    received_items_notification: jingle/nothing/message - Sets the received_items_notification.
    default_player_name: player_name/custom/random/vanilla - Sets the default player name. with player_name, tries to use the AP player name.
    default_rival_name: random/custom/player_name/vanilla - Sets the default rival name. with random, picks from one of the players in the AP.
    default_gender: vanilla/male/female/random - Sets the default gender.

    The text_speed, sound, battle_scene, battle_style, button_mode, text_frame, and received_items_notification
    options can additionally be modifier in the in-game options menu.

    for the player and rival names, the maximum length is 7 characters, and
    the following characters are accepted:
    all alphanumeric characters (A-Z, a-z, 0-9),
    and the following symbols: , . ' - : ; ! ? " ( ) ~ @ # % + * / =,
    and as spaces. Additionally, some special characters, for example most accented vowels, are accepted.

    If the player or rival names do not satisfy these constraints, the game will use its original
    behaviour, where the player or rival names are entered during the starting cutscene.
    """
    display_name = "Game Options"
    default = {
        "text_speed": "mid",
        "sound": "stereo",
        "battle_scene": "on",
        "battle_style": "shift",
        "button_mode": "normal",
        "text_frame": 1,
        "received_items_notification": "jingle",
        "default_player_name": "player_name",
        "default_rival_name": "random",
        "default_gender": "vanilla",
    }

    def __getattr__(self, name: str) -> Any:
        if name in GameOptions.default:
            return self.get(name, GameOptions.default[name])
        else:
            raise AttributeError(name, self)

class RequireFlyForNorthSinnoh(Toggle):
    """
    Require HM02 Fly (and the badge if necessary) to logically access North Sinnoh.
    """
    display_name = "North Sinnoh Requires Fly"

class RequireParcelCouponsCheckRoute203(DefaultOnToggle):
    """
    Whether Looker blocks you from exiting Jubilife city towards Route 203 if you
    haven't delivered the parcel and exchanged the three coupons.
    """
    display_name = "Require Parcel and Coupons for Route 203 from Jubilife"

class RemoteItems(Choice):
    """
    Whether local items should be given in-game, or sent by the server.
    This overrides the show randomized progression items option: all items are shown.
    It is highly recommended to use nothing for received items notification, otherwise
    you will be notified twice for each item.

    Choices:
    - off: no items are remote.
    - only_randomized: only randomized items are remote.
    - only_randomized_or_progression: only randomized items or progression items are remote.
    - all: all (randomizable) items are remote.
    """
    display_name = "Remote Items"
    default = 0
    option_off = 0
    option_only_randomized = 1
    option_only_randomized_or_progression = 2
    option_all = 3

class FPS60(Toggle):
    """
    Whether the 60 FPS patch should be applied.

    This option can also be modified in the in-game options menu.
    """
    display_name = "60 FPS"

class AddSSTicket(Toggle):
    """
    Add the S.S. Ticket to the item pool.
    The S.S. ticket can be used to travel to the fight area before defeating Cynthia.
    Note: the S.S. Ticket is required to access the fight area, but
    if it is not randomized, it is given by the player's mom
    after defeating Cynthia.
    """
    display_name = "Add S.S. Ticket"

class NationalDexNumMons(Range):
    """
    Number of seen regional Pokémon required to complete the Regional
    Pokédex. (This is when you can receive the National Dex from Oak)
    """
    display_name = "National Dex Num Mons"
    range_start = 1
    # range end will be expanded as more encounters are added.
    range_end = 210
    default = 60

class AddMarshPass(Toggle):
    """
    Add the Marsh Pass item to the game. The Marsh pass gives free access to the Great Marsh,
    but if it is enabled, it is required to enter. (i.e., you cannot pay to enter the Great Marsh
    if this option is enabled)
    """
    display_name = "Add Marsh Pass"

class SunyshoreEarly(Toggle):
    """
    With this option enabled, access to Sunyshore City via Valor Lakefront is no longer blocked
    until the Distortion World has been cleared.
    """
    display_name = "Early Sunyshore"

class AddStorageKey(Toggle):
    """
    Add the Storage Key item to the item pool. This allows access to the warehouse portion
    of the Veilstone Galactic HQ without having to clear all three lake events.
    """
    display_name = "Add Storage Key"

class UnownsOption(Choice):
    """
    How the Maniac Tunnel is handled.

    Vanilla: 26 Unown forms must be encountered before the Maniac Tunnel is traversable.
    Item: 28 "Unown Form" items are added to the item pool. 26 of them must be collected
    before the Maniac Tunnel is traversable.
    None: The Maniac Tunnel is always traversable.
    """
    display_name = "Unowns Choice"
    option_vanilla = 0
    option_item = 1
    option_none = 2
    default = 1

class AddBag(Toggle):
    """
    Add the bag to the item pool. Before obtaining it, the bag cannot be opened in the menu.
    """
    display_name = "Add Bag"

class PastoriaBarriers(Toggle):
    """
    Add barriers in Route 212 and Route 214, blocking the path to Pastoria City
    until the player has surf.
    """
    display_name = "Pastoria Barriers"

class HMCutIns(Toggle):
    """
    Whether HM Cut-Ins should be played.

    This option can also be modified in the in-game options menu.
    """
    display_name = "HM Cut-Ins"

class BuckPos(Toggle):
    """
    Whether Buck should be moved to the end of Stark Mountain.

    This option can also be modified in the in-game options menu.
    """
    display_name = "Buck Position"

class HBSpeed(Range):
    """
    The speed multiplier of the health bar.

    This option can also be modified in the in-game options menu.
    """
    display_name = "Healthbar Speed"
    range_start = 1
    range_end = 16
    default = 1

class NormalizeEncounters(DefaultOnToggle):
    """
    In the vanilla game, encounter table entries have varying probabilities, from 20% down to 1%.
    This option will normalize these, so they all have the same probability. The normalized
    probabilities are 1/12 for each entry in the land table, and 1/5 for each entry in the water
    and rod tables.

    This option is modifiable in the in-game options menu.

    Note: this does not mean that there are twelve encounter slots, and a 1/12 chance for each slot.
    Often there will only be two or three encounter slots per route, occupying all twelve entries
    in the encounter table. This option only means that the *smallest* possible probability for any
    slot will be 1/12. (except for special encounters, where there may be more or less table
    entries)
    """
    display_name = "Normalize Encounters"

class InstantText(Toggle):
    """
    Have text scroll instantly.

    This option is modifiable in the in-game options menu.
    """
    display_name = "Instant Text"

class HoldAToAdvance(Toggle):
    """
    You no longer need to press A to advance text, holding it will suffice. (Same for B)

    This option is modifiable in the in-game options menu.
    """
    display_name = "Hold A to Advance"

class ReusableTms(Toggle):
    """TMs are reusable."""
    display_name = "Reusable TMs"

class AlwaysCatch(Toggle):
    """
    Have a 100% chance of catching any encounter.

    This option is modifiable in the in-game options menu.
    """
    display_name = "Always Catch"

class StartWithSwarms(DefaultOnToggle):
    """
    Start the game with swarms enabled.
    Note: swarms will only be enabled after you obtain the poffin case,
    which is when you can control their locations.
    """
    display_name = "Start With Swarms"

class CanResetLegendariesInAPHelper(DefaultOnToggle):
    """Can reset roamers with the AP Helper. (Present in the 2nd floor of any Pokémon Centre)"""
    display_name = "Can Reset Roamers in AP Helper"

class EvoItemsShopInAPHelper(DefaultOnToggle):
    """Evolution items shop is available with the AP Helper. (Present in the 2nd floor of any Pokémon Centre)"""
    display_name = "Evolution Item Shop in AP Helper"

class CheatsEnabled(Toggle):
    """Client cheats are enabled."""
    display_name = "Cheats Enabled"

class GuaranteedEscape(Toggle):
    """
    You will always be able to escape from wild encounters.

    This option is modifiable in the in-game options menu.
    """
    display_name = "Guaranteed Escape."

class TalkTrainersWithoutFight(Toggle):
    """
    You can talk to trainers without having to fight them.
    This only applies when you talk to them, not if they spot you.
    Note: them spotting you can be disabled by the blind trainers option.

    This option is modifiable in the in-game options menu.
    """
    display_name = "Talk to Trainers without Fighting Them"

class RandomizeEncounters(Toggle):
    """Randomize encountered Pokémon. This does not affect static legendaries, like Giratina."""
    display_name = "Randomize Encounters"


class InLogicEncounters(OptionSet):
    """
    Which methods/variations of encounters are in logic.
    """
    display_name = "In Logic Encounters"
    default = {"surf", "old_rod", "good_rod", "super_rod", "poke_radar", "ruby", "sapphire", "night", "emerald", "firered", "leafgreen", "day", "swarms", "great_marsh_observatory", "great_marsh_observatory_national_dex", "regular_honey_tree", "munchlax_honey_tree", "feebas_fishing", "trophy_garden", "odd_keystone", "roamers"}
    valid_keys = ["surf", "old_rod", "good_rod", "super_rod", "poke_radar", "ruby", "sapphire", "night", "emerald", "firered", "leafgreen", "day", "swarms", "great_marsh_observatory", "great_marsh_observatory_national_dex", "regular_honey_tree", "munchlax_honey_tree", "feebas_fishing", "trophy_garden", "odd_keystone", "roamers"]

class EncounterSpeciesBlacklist(SpeciesBlacklist):
    """
    Specify the banned encounter species.
    The whitelist has precedence over this.
    This has no effect if starters are not randomized.

    The species names should be entered entirely in lowercase.
    Spaces should be replaced by underscores. For example,
    Mr. Mime would be mr_mime.

    legendaries, all lowercase, will be interpreted as banning all legendary
    species.

    Currently, this cannot include kecleon, geodude, or munchlax.
    """
    valid_keys = list(species.keys() - {"kecleon", "geodude", "munchlax"}) + ["legendaries"]

class RandomizeTrainerParties(Toggle):
    """Randomize trainer party members."""
    display_name = "Randomize Trainer Parties"

class TrainerPartyBlacklist(SpeciesBlacklist):
    """
    Specify the banned trainer party species.
    The whitelist has precedence over this.
    This has no effect if starters are not randomized.

    The species names should be entered entirely in lowercase.
    Spaces should be replaced by underscores. For example,
    Mr. Mime would be mr_mime.

    legendaries, all lowercase, will be interpreted as banning all legendary
    species.
    """
    valid_keys = list(species) + ["legendaries"]


class RandomizeStarters(Toggle):
    """Randomize starter Pokémon."""
    display_name = "Randomize Starters"

class RequireTwoLevelEvolutionStarters(Toggle):
    """If the starters are randomized, require that they all be two-level-evolution species."""
    display_name = "Require Two Level Evolution Starters"

class StarterWhitelist(OptionSet):
    """
    Specify the possible starters that can be randomized.
    This has precedence over the blacklist and the require two-level-evolution
    species.
    This has no effect if starters are not randomized.

    The species names should be entered entirely in lowercase.
    Spaces should be replaced by underscores. For example,
    Mr. Mime would be mr_mime.

    Note: legendaries is **not** a valid key for this option.
    """
    display_name = "Starter Whitelist"
    valid_keys = list(species)

class StarterBlacklist(SpeciesBlacklist):
    """
    Specify the banned starters.
    The whitelist has precedence over this.
    This has no effect if starters are not randomized.

    The species names should be entered entirely in lowercase.
    Spaces should be replaced by underscores. For example,
    Mr. Mime would be mr_mime.

    legendaries, all lowercase, will be interpreted as banning all legendary
    species.
    """
    display_name = "Starter Blacklist"
    valid_keys = list(species) + ["legendaries"]

class RandomizeBunearyInIntro(DefaultOnToggle):
    """Randomize the species of the Pokémon that is shown in the intro."""
    display_name = "Randomize Intro Pokémon"

class Trainersanity(Toggle):
    """
    Each trainer adds a location to the game. These locations are
    filled with nuggets by default.
    """
    display_name = "Trainersanity"

class DexsanityCount(NamedRange):
    """
    How many dexsanity locations there will be.
    """
    display_name = "Dexsanity Count"
    default = 0
    range_start = 0
    range_end = 493
    special_range_names = {
        "none": default,
        "full": range_end,
    }

class DexsanityMode(Choice):
    """
    The dexsanity mode.

    Options:
    - noreq: no items are required to trigger dexsanity locations.
    - req: the Pokedex (or National Dex for non-regional species) is required
           to trigger dexsanity locations.
    - req_noprompt: same as req, but when you initially get the Pokedex
                    or National Dex, do not prompt for each already seen
                    dexsanity species.
    """
    display_name = "Dexsanity Mode"
    default = 1
    option_noreq = 1
    option_req = 2
    option_req_noprompt = 3

class RandomizeRoamers(Toggle):
    """
    Randomize roaming Pokemon.
    """
    display_name = "Randomize Roamers"

class RoamerBlacklist(SpeciesBlacklist):
    """
    Specify the banned roaming Pokemon species.
    The whitelist has precedence over this.
    This has no effect if starters are not randomized.

    The species names should be entered entirely in lowercase.
    Spaces should be replaced by underscores. For example,
    Mr. Mime would be mr_mime.

    legendaries, all lowercase, will be interpreted as banning all legendary
    species.
    """
    valid_keys = list(species) + ["legendaries"]
    display_name = "Roamer Blacklist"

class InLogicEvolutionMethods(OptionSet):
    """
    Evolution methods that are in logic.
    """
    display_name = "In-Logic Evolution Methods"
    default = {"level", "level_atk_gt_def", "level_atk_eq_def", "level_atk_lt_def", "level_pid_low", "level_pid_high", "level_ninjask", "level_shedinja", "level_male", "level_female", "trade_with_held_item", "use_item", "use_item_male", "use_item_female", "level_with_held_item_day", "level_with_held_item_night", "level_happiness", "level_happiness_day", "level_happiness_night", "trade", "level_beauty", "level_magnetic_field", "level_moss_rock", "level_ice_rock", "level_know_move", "level_species_in_party" }
    valid_keys = {"level", "level_atk_gt_def", "level_atk_eq_def", "level_atk_lt_def", "level_pid_low", "level_pid_high", "level_ninjask", "level_shedinja", "level_male", "level_female", "trade_with_held_item", "use_item", "use_item_male", "use_item_female", "level_with_held_item_day", "level_with_held_item_night", "level_happiness", "level_happiness_day", "level_happiness_night", "trade", "level_beauty", "level_magnetic_field", "level_moss_rock", "level_ice_rock", "level_know_move", "level_species_in_party" }

class AddHMReader(Choice):
    """
    Add the HM Reader item. The HM Reader is an item that lets you use field moves without teaching them.

    Options:
    - no: Don't add the HM Reader item.
    - itempool: Add the HM Reader item to the itempool.
    - precollected: Start with the HM Reader item.
    """
    option_no = 0
    option_itempool = 1
    option_precollected = 2
    default = option_no

class HMReaderMode(Choice):
    """
    Mode for the HM Reader. The HM Reader is an item that lets you use field moves without teaching them.

    Options:
    - req_mon: require a Pokemon in your party to which you can teach the move, in order for the HM Reader to use it.
    - noreq_mon: do not require a Pokemon in your party to which you can teach the move.
    """
    option_req_mon = 0
    option_noreq_mon = 1
    default = option_req_mon

slot_data_options: Sequence[str] = [
    "hms",
    "badges",
    "overworlds",
    "hiddens",
    "npc_gifts",
    "key_items",
    "rods",
    "poketch_apps",
    "running_shoes",
    "bicycle",
    "pokedex",
    "accessories",
    "cartridges",
    "time_items",

    "hm_badge_requirement",
    "remove_badge_requirements",
    "visibility_hm_logic",
    "dowsing_machine_logic",
    "north_sinnoh_fly",
    "parcel_coupons_route_203",
    "regional_dex_goal",
    "early_sunyshore",
    "pastoria_barriers",
    "reusable_tms",
    "start_with_swarms",
    "can_reset_legendaries_in_ap_helper",
    "evo_items_shop_in_ap_helper",

    "hm_reader",
    "hm_reader_mode",

    "randomize_starters",
    "require_two_level_evolution_starters",
    "starter_whitelist",
    "starter_blacklist",
    "randomize_intro_mon",

    "randomize_encounters",
    "in_logic_encounters",
    "encounter_species_blacklist",
    "dexsanity_count",
    "dexsanity_mode",
    "in_logic_evolution_methods",

    "randomize_roamers",
    "roamer_blacklist",
    "roamer_blacklist",

    "trainersanity",
    "randomize_trainer_parties",
    "trainer_party_blacklist",

    "death_link",

    "cheats_enabled",

    "master_repel",
    "s_s_ticket",
    "marsh_pass",
    "storage_key",
    "bag",
    "unown_option",

    "remote_items",

    "goal",
]

class PokemonPlatinumDeathLink(DeathLink):
    __doc__ = DeathLink.__doc__ + "\n\n    In Pokémon Platinum, blacking out sends a death and receiving a death causes you to black out.\n" # type: ignore

@dataclass
class PokemonPlatinumOptions(PerGameCommonOptions):
    hms: RandomizeHms
    badges: RandomizeBadges
    overworlds: RandomizeOverworlds
    hiddens: RandomizeHiddenItems
    npc_gifts: RandomizeNpcGifts
    key_items: RandomizeKeyItems
    rods: RandomizeRods
    poketch_apps: RandomizePoketchApps
    running_shoes: RandomizeRunningShoes
    bicycle: RandomizeBicycle
    pokedex: RandomizePokedex
    accessories: RandomizeAccessories
    cartridges: RandomizeCartridges
    time_items: RandomizeTimeItems

    hm_badge_requirement: HmBadgeRequirements
    remove_badge_requirements: RemoveBadgeRequirement
    visibility_hm_logic: VisibilityHmLogic
    dowsing_machine_logic: DowsingMachineLogic
    north_sinnoh_fly: RequireFlyForNorthSinnoh
    parcel_coupons_route_203: RequireParcelCouponsCheckRoute203
    regional_dex_goal: NationalDexNumMons
    early_sunyshore: SunyshoreEarly
    pastoria_barriers: PastoriaBarriers
    reusable_tms: ReusableTms
    start_with_swarms: StartWithSwarms
    can_reset_legendaries_in_ap_helper: CanResetLegendariesInAPHelper
    evo_items_shop_in_ap_helper: EvoItemsShopInAPHelper
    
    hm_reader: AddHMReader
    hm_reader_mode: HMReaderMode

    randomize_starters: RandomizeStarters
    require_two_level_evolution_starters: RequireTwoLevelEvolutionStarters
    starter_whitelist: StarterWhitelist
    starter_blacklist: StarterBlacklist
    randomize_intro_mon: RandomizeBunearyInIntro

    randomize_encounters: RandomizeEncounters
    in_logic_encounters: InLogicEncounters
    encounter_species_blacklist: EncounterSpeciesBlacklist
    dexsanity_count: DexsanityCount
    dexsanity_mode: DexsanityMode
    in_logic_evolution_methods: InLogicEvolutionMethods

    randomize_roamers: RandomizeRoamers
    roamer_blacklist: RoamerBlacklist

    trainersanity: Trainersanity
    randomize_trainer_parties: RandomizeTrainerParties
    trainer_party_blacklist: TrainerPartyBlacklist

    game_options: GameOptions
    blind_trainers: BlindTrainers
    hm_cut_ins: HMCutIns
    fps60: FPS60
    buck_pos: BuckPos
    hb_speed: HBSpeed
    normalize_encounters: NormalizeEncounters
    instant_text: InstantText
    hold_a_to_advance: HoldAToAdvance
    always_catch: AlwaysCatch
    guaranteed_escape: GuaranteedEscape
    talk_trainers_without_fight: TalkTrainersWithoutFight
    exp_multiplier: ExpMultiplier

    death_link: PokemonPlatinumDeathLink

    cheats_enabled: CheatsEnabled

    master_repel: AddMasterRepel
    s_s_ticket: AddSSTicket
    marsh_pass: AddMarshPass
    storage_key: AddStorageKey
    bag: AddBag
    unown_option: UnownsOption

    remote_items: RemoteItems

    goal: Goal

    def requires_badge(self, hm: str) -> bool:
        return self.hm_badge_requirement.value == 1 or hm.lower() in self.remove_badge_requirements

    def validate(self) -> None:
        if self.pastoria_barriers:
            if not self.badges and self.requires_badge("SURF"):
                raise OptionError(f"cannot enable Pastoria barriers if Surf requires the Fen Badge and badges are not randomized.")
            if not (self.hms or self.key_items.are_most_randomized()):
                raise OptionError(f"cannot enable Pastoria barriers if both HMs and Key Items are not randomized.")
        if not (self.overworlds or self.hiddens or self.npc_gifts or self.key_items.value > 0 or self.poketch_apps):
            raise OptionError(f"at least one of overworlds, hiddens, npc_gifts, key_items, or poketch apps must be enabled")
        if self.bag and self.dowsing_machine_logic and not (self.overworlds or self.npc_gifts or self.rods or self.running_shoes or self.pokedex or self.key_items.value > 0):
            raise OptionError(f"if the bag is enabled, then at least one of overworlds, npc_gifts, rods, running_shoes, pokedex, key_items must be enabled")

        # validate game options
        game_opts = self.game_options
        if game_opts.default_gender not in {"male", "female", "random", "vanilla"}:
            raise OptionError(f"invalid default gender: \"{game_opts.default_gender}\"")
        if game_opts.text_speed not in {"fast", "slow", "mid"}:
            raise OptionError(f"invalid text speed: \"{game_opts.text_speed}")
        if game_opts.sound not in {"mono", "stereo"}:
            raise OptionError(f"invalid sound: \"{game_opts.sound}\"")
        if game_opts.battle_scene not in {False, "off", True, "on"}:
            raise OptionError(f"invalid battle scene: \"{game_opts.battle_scene}\"")
        if game_opts.battle_style not in {"set", "shift"}:
            raise OptionError(f"invalid battle style: \"{game_opts.battle_style}\"")
        if game_opts.button_mode not in {"start=x", "l=a", "normal"}:
            raise OptionError(f"invalid button mode: \"{game_opts.button_mode}\"")
        text_frame = game_opts.text_frame
        if game_opts.text_frame not in set(range(1, 21)) | {"random"}:
            raise OptionError(f"invalid text frame: \"{text_frame}\"")
        if game_opts.received_items_notification not in {"nothing", "message", "jingle"}:
            raise OptionError(f"invalid received items notification: \"{game_opts.received_items_notification}\"")

        if not self.randomize_encounters and not {"great_marsh_observatory_national_dex", "munchlax_honey_tree"} <= self.in_logic_encounters.value:
            raise OptionError("if encounters are not randomized, then great_marsh_observatory_national_dex and munchlax_honey_tree must both be in logic")
        rm_set = frozenset(regional_mons)
        if self.randomize_encounters and self.randomize_trainer_parties and len(rm_set - (self.encounter_species_blacklist.blacklist() & self.trainer_party_blacklist.blacklist())) < max(50, self.regional_dex_goal.value):
            raise OptionError(f"encounter species blacklist and trainer party blacklist are too restrictive: can't get enough regional species.")
        elif self.randomize_encounters:
            if not self.pokedex:
                in_logic_trainer_mons = {p.species
                    for rd in regions.values()
                    for trainer in rd.trainers
                    if not trainer_requires_national_dex(trainer)
                    for p in trainer_party_supporting_starters(trainer)
                    if p.species in rm_set
                }
                if len(rm_set - self.encounter_species_blacklist.blacklist() - in_logic_trainer_mons) <  self.regional_dex_goal.value - len(in_logic_trainer_mons):
                    raise OptionError(f"encounter species blacklist is too restrictive: can't get enough regional species.")
            in_logic_trainer_mons = {p.species
                for rd in regions.values()
                for trainer in rd.trainers
                for p in trainer_party_supporting_starters(trainer)
                if p.species in rm_set
            }
            if len(rm_set - self.encounter_species_blacklist.blacklist() - in_logic_trainer_mons) < max(50, self.regional_dex_goal.value) - len(in_logic_trainer_mons):
                raise OptionError(f"encounter species blacklist is too restrictive: can't get enough regional species.")
        elif self.randomize_trainer_parties:
            if not self.pokedex:
                acc_suc = set() if self.start_with_swarms else {"swarms"}
                in_logic_encounter_mons = {slot.species
                    for rd in regions.values()
                    if rd.header in encounters and rd.header not in national_dex_requiring_encs \
                    for type, table in encounter_type_pairs
                    if type != "water" or table in self.in_logic_encounters
                    for i, slot in enumerate(getattr(encounters[rd.header], table))
                    if not slot.accessibility or (set(slot.accessibility) - acc_suc) & self.in_logic_encounters.value
                    if slot.species in rm_set
                } | {spec
                    for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
                    if nm in self.in_logic_encounters and nm not in special_encounters.requiring_national_dex
                    for spec in getattr(special_encounters, nm)
                    if spec in rm_set
                }
                if len(rm_set - self.trainer_party_blacklist.blacklist() - in_logic_encounter_mons) < self.regional_dex_goal.value - len(in_logic_encounter_mons):
                    raise OptionError(f"trainer party blacklist is too restrictive: can't get enough regional species.")
            in_logic_encounter_mons = {slot.species
                for rd in regions.values()
                if rd.header in encounters \
                for type, table in encounter_type_pairs
                if type != "water" or table in self.in_logic_encounters
                for i, slot in enumerate(getattr(encounters[rd.header], table))
                if not slot.accessibility or set(slot.accessibility) & self.in_logic_encounters.value
                if slot.species in rm_set
            } | {spec
                for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
                if nm in self.in_logic_encounters
                for spec in getattr(special_encounters, nm)
                if spec in rm_set
            }
            if len(rm_set - self.trainer_party_blacklist.blacklist() - in_logic_encounter_mons) < max(50, self.regional_dex_goal.value) - len(in_logic_encounter_mons):
                raise OptionError(f"trainer party blacklist is too restrictive: can't get enough regional species.")
        else:
            if not self.pokedex:
                acc_suc = set() if self.start_with_swarms else {"swarms"}
                in_logic_encounter_mons = {slot.species
                    for rd in regions.values()
                    if rd.header in encounters and rd.header not in national_dex_requiring_encs \
                    for type, table in encounter_type_pairs
                    if type != "water" or table in self.in_logic_encounters
                    for slot in getattr(encounters[rd.header], table)
                    if not slot.accessibility or (set(slot.accessibility) - acc_suc) & self.in_logic_encounters.value
                    if slot.species in rm_set
                }
                in_logic_trainer_mons = {p.species
                    for rd in regions.values()
                    for trainer in rd.trainers
                    if not trainer_requires_national_dex(trainer)
                    for p in trainer_party_supporting_starters(trainer)
                    if p.species in rm_set
                }
                if len(in_logic_encounter_mons | in_logic_trainer_mons) < self.regional_dex_goal.value:
                    raise OptionError(f"regional dex goal is too high. not enough encounters to fill it")
            in_logic_encounter_mons = {slot.species
                for rd in regions.values()
                if rd.header in encounters \
                for type, table in encounter_type_pairs
                if type != "water" or table in self.in_logic_encounters
                for slot in getattr(encounters[rd.header], table)
                if not slot.accessibility or set(slot.accessibility) & self.in_logic_encounters.value
                if slot.species in rm_set
            }
            in_logic_trainer_mons = {p.species
                for rd in regions.values()
                for trainer in rd.trainers
                for p in trainer_party_supporting_starters(trainer)
                if p.species in rm_set
            }
            if len(in_logic_encounter_mons | in_logic_trainer_mons) < max(50, self.regional_dex_goal.value):
                raise OptionError(f"regional dex goal is too high. not enough encounters to fill it")
        if self.randomize_encounters:
            amity_square_mons = {
                "pikachu",
                "clefairy",
                "jigglypuff",
                "psyduck",
                "torchic",
                "shroomish",
                "skitty",
                "turtwig",
                "grotle",
                "torterra",
                "chimchar",
                "monferno",
                "infernape",
                "piplup",
                "prinplup",
                "empoleon",
                "pachirisu",
                "drifloon",
                "buneary",
                "happiny",
            } - self.encounter_species_blacklist.blacklist()
            if not amity_square_mons:
                raise OptionError("at least one Amity Square species must be able to be encountered")
        if self.dexsanity_count:
            if self.randomize_encounters:
                slots = len({(rd.header, table, i)
                    for _, rd in regions.items()
                    if rd.header in encounters \
                        and (self.unown_option != UnownsOption.option_vanilla or not rd.header.startswith("solaceon_ruins"))
                    for type, table in encounter_type_pairs
                    if type != "water" or table in self.in_logic_encounters
                    for i, slot in enumerate(getattr(encounters[rd.header], table))
                    if not slot.accessibility or set(slot.accessibility) & self.in_logic_encounters.value
                })
                speenc_slots = len({(nm, i)
                    for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
                    if nm in self.in_logic_encounters
                    for i in range(len(getattr(special_encounters, nm)))
                })
                if min(slots + speenc_slots, len(species) - len(self.encounter_species_blacklist.blacklist())) < self.dexsanity_count:
                    raise OptionError("dexsanity count larger than number of in-logic encounter slots")
            else:
                in_logic_encounter_mons = {slot.species
                    for rd in regions.values()
                    if rd.header in encounters \
                    for type, table in encounter_type_pairs
                    if type != "water" or table in self.in_logic_encounters
                    for i, slot in enumerate(getattr(encounters[rd.header], table))
                    if not slot.accessibility or set(slot.accessibility) & self.in_logic_encounters.value
                } | {spec
                    for nm in ["regular_honey_tree", "munchlax_honey_tree", "trophy_garden", "great_marsh_observatory", "great_marsh_observatory_national_dex", "feebas_fishing", "odd_keystone"]
                    for spec in getattr(special_encounters, nm)
                }
                if len(in_logic_encounter_mons) < self.dexsanity_count:
                    raise OptionError("dexsanity count larger than in-logic species count")
        if self.randomize_roamers and len(species.keys() - self.roamer_blacklist.blacklist()) < 5:
            raise OptionError(f"roamer blacklist too restrictive")

        if self.randomize_starters:
            if 0 < len(self.starter_whitelist.value) < 3:
                raise OptionError(f"starter whitelist must contain at least three values")
            elif len(self.starter_whitelist.value) == 0 and len(species.keys() - self.starter_blacklist.blacklist()) < 3:
                raise OptionError(f"starter blacklist too restrictive")

    def save_options(self) -> MutableMapping[str, Any]:
        return self.as_dict(*slot_data_options)

    def load_options(self, slot_data: Mapping[str, Any]) -> None:
        for key in slot_data_options:
            if isinstance(getattr(self, key), OptionSet):
                getattr(self, key).value = frozenset(slot_data[key])
            else:
                getattr(self, key).value = slot_data[key]
