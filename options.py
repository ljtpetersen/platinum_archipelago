from dataclasses import dataclass
from Options import Choice, DefaultOnToggle, OptionDict, OptionSet, PerGameCommonOptions, Toggle

class RandomizeHms(DefaultOnToggle):
    display_name = "Randomize HMs"

class RandomizeBadges(DefaultOnToggle):
    display_name = "Randomize Badges"

class RandomizeOverworlds(DefaultOnToggle):
    display_name = "Randomize Overworlds"

class RandomizeHiddenItems(Toggle):
    display_name = "Randomize Hidden Items"

class RandomizeNpcGifts(DefaultOnToggle):
    display_name = "Randomize NPC Gifts"

class RandomizeKeyItems(Choice):
    display_name = "Randomize Key Items"
    default = 1
    option_vanilla = 0
    option_most = 1
    option_all = 2

    def are_most_randomized(self) -> bool:
        return self.value >= self.option_most

class RandomizeRods(DefaultOnToggle):
    display_name = "Randomize Rods"

class RandomizePoketchApps(DefaultOnToggle):
    display_name = "Randomize Poketch Apps"

class HmBadgeRequirements(DefaultOnToggle):
    display_name = "Require Badges for HMs"

class RemoveBadgeRequirement(OptionSet):
    """
    Specify which HMs do not require a badge to use. This overrides the HM Badge Requirements setting.

    HMs should be provided in the form: "FLY", "WATERFALL", "ROCK_SMASH", etc.
    """
    display_name = "Remove Badge Requirement"
    valid_keys = ["CUT", "FLY", "SURF", "STRENGTH", "DEFOG", "ROCK_SMASH", "WATERFALL", "ROCK_CLIMB"]

class VisibilityHmLogic(DefaultOnToggle):
    display_name = "Logically Require Flash or Defog for Applicable Regions"

class DowsingMachineLogic(DefaultOnToggle):
    display_name = "Logically Require Dowsing Machine for Hidden Items"

class Goal(Choice):
    display_name = "Goal"
    default = 0
    option_champion = 0

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

    for the player and rival names, the following characters are accepted:
    all alphanumeric characters (A-Z, a-z, 0-9),
    and the following symbols: , . ' - : ; ! ? " ( ) ~ @ # % + * / =,
    and as spaces.
    as well, there are some special sequences.
      \\" is an opening double-quotation mark
      \\' is an opening single-quotation mark
      \\. is a centred dot (centred vertically)
      \\Z are two superimposed Zs (as in sleep)
      ^ is an upwards arrow
      \\v is a downwards arrow
      {MALE} is the male sign
      {FEMALE} is the female sign
      {...} are ellipsis
      {O.} is a circle with a dot inside it. {.O} also works
      {CIRCLE} is a circle
      {SQUARE} is a square
      {TRIANGLE} is a triangle
      {DIAMOND} is a diamond (hollow)
      {SPADE} is a spade
      {CLUB} is a club
      {HEART} is a heart
      {SUIT DIAMOND} is a diamond (filled)
      {STAR} is a star
      {NOTE} is a music note (1/8)
      {SUN} is a sun
      {CLOUD} is a cloud
      {UMBRELLA} is an umbrella
      {SILHOUETTE} is a really bad looking silhouette
      {SMILE} is a smiling face
      {LAUGH} is a laughing face
      {UPSET} is an upset face
      {FROWN} is a frowning face
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

    hm_badge_requirement: HmBadgeRequirements
    remove_badge_requirements: RemoveBadgeRequirement
    visibility_hm_logic: VisibilityHmLogic
    dowsing_machine_logic: DowsingMachineLogic
    goal: Goal
    game_options: GameOptions

    def requires_badge(self, hm: str) -> bool:
        return self.hm_badge_requirement.value == 1 or hm in self.remove_badge_requirements
