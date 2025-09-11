# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2025-09-11
### Fixed
* The Pokétch App locations in Sunyshore City now have the correct rules.

## [0.1.3] - 2025-09-10
### Fixed
* The value of the `pastoria_barriers` option is now correctly written to the ROM.
* The person at the entrance to the Hearthome City Gym now correctly checks that you have
defeated the gym leader for their dialogue, rather than if you have the badge requirements to use
the corresponding HM.

## [0.1.2] - 2025-09-09
### Fixed
* Unrandomized non-progression items are no longer added if remote items are disabled.

## [0.1.1] - 2025-09-09
### Fixed
* Lake Valor Cavern exits.
* Unown File locations now require the Dowsing Machine if the corresponding option is enabled.
### Changed
* Some changes have been made to the ROM. These theoretically should not have changed anything in the
gameplay, but this cannot be guaranteed.

## [0.1.0] - 2025-09-07
### Added
* An option to show/hide unrandomized progression items in the chat.
* A remote items option.
* An option to logically require fly for North Sinnoh.
* An option to stop Looker from blocking the East exit to Jubilife City.
* A 60 FPS patch option.
* Veilstone Department Store locations.
* Pal Pad Location in Pokémon Center Basement.
* An option to add the S.S. Ticket to the item pool.
* An option to set the completion goal of the regional Pokédex.
* An option to allow access to Sunyshore City early.
* An option to add the Storage Key to the item pool.
* An option to add the Marsh Pass to the item pool.
* An option to add the Bag to the item pool.
* An option to customize the requirements for the Maniac Tunnel.
* Certain options can now also be adjusted in-game.
* Post-game locations.
* An option to move Buck to the back of Stark Mountain.
* Accessory items and locations.
* Some repeatable locations.
* An option to speed up the healthbar scrolling.
### Fixed
* Incorrect rules on Route 208 hidden Star Piece.
* The secret entrance to Wayward Cave no longer optionally requires flash.
* The Archipelago Unit Test suite now runs.
* The Pokédex and Bag are no longer accessible until the player receives a starter Pokémon.
* Issue where items for other Platinum worlds are also given to the local world.
* Old Charm Location in Route 210 now requires SecretPotion in logic.
* Super Repel on Route 210 South now logically requires the Bicycle.
* TM27 from Rowan will now be detected even if it was given when the client was not connected.
* Experience gained via Exp. Share is not affected by experience multiplier.
* Floaroma Town now also exits to Route 204 North.
* Old Château can no longer be accessed while partnered with Cheryl.
* Grunts blocking Mt. Coronet Basement are now properly removed.
* Logic error regarding order of access of lakes after Canalave event.
* Entering Route 228 crashes the game.
* Issue with Pokédex Location in Pokémon Research Lab.
### Changed
* Access to Pokémon Center Basements in Jubilife and Sandgem are no longer blocked before defeating Roark.
* The S.S. Spiral can now be used if the player has defeated Cynthia, *or* of they have the S.S. Ticket.
* Items which are added by options, but for which no location can be found for, are now added to the starting inventory. (precollected)
* The intro is now abridged.

## [0.0.2] - 2025-08-28
### Added
* Starting inventory support.
* Item groups.
### Fixed
* Crashes when giving multiple bag items (like `Rare Candy x15`) with `nothing` item receiving notification option.
* Crashes when giving multiple Pokétches with `jingle` and `nothing` item receiving notification options.
* Generation error when using `poketch_apps = false`.
* Issues running data generation with Python version < 3.12.
* Hardlock when obtaining the Pokétch from a local location.
* Random text frame is now random.
* Added connection from Route 207 to Route 207 South.
* A potential issue when getting multiple journals.
* A bug where, when using `nothing` item receiving notification, the upgradable Pokédex would
skip over the forms, and the second one would give the National Pokédex.
### Changed
* Game options now use the default value if there is no corresponding entry in the YAML.
* Game options now raise exceptions if invalid values are entered.
* Locations which are disabled by options are now properly tracked, and will be logged in the client/server when checked.

## [0.0.1] - 2025-08-26
The first release of this project.

[0.1.3]: https://github.com/ljtpetersen/platinum_archipelago/compare/v0.1.3...v0.1.2
[0.1.2]: https://github.com/ljtpetersen/platinum_archipelago/compare/v0.1.2...v0.1.1
[0.1.1]: https://github.com/ljtpetersen/platinum_archipelago/compare/v0.1.1...v0.1.0
[0.1.0]: https://github.com/ljtpetersen/platinum_archipelago/compare/v0.1.0...v0.0.2
[0.0.2]: https://github.com/ljtpetersen/platinum_archipelago/compare/v0.0.2...v0.0.1
[0.0.1]: https://github.com/ljtpetersen/platinum_archipelago/releases/tag/v0.0.1
