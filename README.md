# Pokémon Platinum Archipelago (AP)

The setup guide is [here](docs/setup_en.md).

## Running From Source
The following are required.
* Python version at least 3.11.
* Additionally to what Archipelago requires, the `pyparsing` library is required.
This can be installed via PIP.

With these, clone this repository in the `worlds` directory of the Archipelago repository.
With every modification to the files in `data_gen` or `data_gen_templates`, and when first cloning the
repository, the `data_gen.py` file must be executed. (Do `python data_gen.py` in the root directory of the repository)

To make the `.apworld` file, run `make` within the root directory of the repository.

## Where Help is Needed
* Better documentation! (`docs/setup_en.md` and `en_Pokemon Platinum.md`)
* Better location labels. In [`data_gen/locations.toml`](data_gen/locations.toml), for each location, simply modify the `label` field.
No other changes necessary.
* Correct logic. There are probably some places with incorrect logic. If you find any of these, open up an issue, and I'll get to fixing it promptly.
* Correct item classifications. Some items may not be classified as `useful`, when they should be. To adjust these, in the `data_gen/items.toml` file,
for each item that should be marked as useful, add the line `classification = "useful"` line.

## What is Missing
* Encounter randomization and level scaling.
* More victory conditions (including rules for fight area).
* Trainersanity.
* Dexsanity.
* Various QOL things.
