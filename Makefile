# Makefile
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

.PHONY: default patches

Q ?= @

ROMS := us_rev0 us_rev1
SOURCES := __init__.py \
	 client.py \
	 items.py \
	 locations.py \
	 options.py \
	 regions.py \
	 rules.py \
	 species.py \
	 rom/__init__.py \
	 rom/encounterdata.py \
	 rom/itemdata.py \
	 rom/speciesdata.py \
	 rom/trainerdata.py \
	 LICENSE
DATA := data_gen/encounters.toml \
       data_gen/event_checks.toml \
       data_gen/items.toml \
       data_gen/locations.toml \
       data_gen/moves.toml \
       data_gen/regions.toml \
       data_gen/rom_interface.toml \
       data_gen/rules.toml \
       data_gen/special_encounters.toml \
       data_gen/species.toml \
       data_gen/trainers.toml \
       data_gen_templates/__init__.py \
       data_gen_templates/charmap.py \
       data_gen_templates/encounters.py \
       data_gen_templates/event_checks.py \
       data_gen_templates/items.py \
       data_gen_templates/locations.py \
       data_gen_templates/moves.py \
       data_gen_templates/regions.py \
       data_gen_templates/rules.py \
       data_gen_templates/special_encounters.py \
       data_gen_templates/species.py \
       data_gen_templates/trainers.py \
       data_gen.py \
       data_gen_rules.py

PATCHES := $(ROMS:%=patches/base_patch_%.bsdiff4)

default: pokemon_platinum.apworld

patches/base_patch_%.bsdiff4: roms/%.nds roms/target.nds
	@echo DIFF $<
	$Q./patch_gen.py $< roms/target.nds $@

data/__init__.py: $(DATA)
	@echo DATA GEN
	$Qpython data_gen.py

apnds/__init__.py: apnds_version.txt
	@echo UDPATE APNDS
	$Qcurl -LSso apnds.tar.gz "https://github.com/ljtpetersen/apnds/releases/download/v`cat apnds_version.txt`/apnds.tar.gz"
	$Qrm -r apnds >/dev/null 2>&1 || true
	$Qtar xzf apnds.tar.gz
	$Qrm apnds.tar.gz
	$Qtouch apnds/__init__.py

patches: $(PATCHES)
	@:

pokemon_platinum.apworld: data/__init__.py apnds/__init__.py $(SOURCES) $(PATCHES)
	@echo MAKE APWORLD
	$Qcd ../..; python Launcher.py "Build APWorlds" "Pokemon Platinum" >/dev/null 2>&1
	$Qcp ../../build/apworlds/pokemon_platinum.apworld .
