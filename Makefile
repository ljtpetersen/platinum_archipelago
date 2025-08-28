
.PHONY: data_gen

Q ?= @

ROMS := us_rev0 us_rev1
SOURCES := __init__.py \
	 client.py \
	 items.py \
	 locations.py \
	 options.py \
	 regions.py \
	 rom.py \
	 rules.py
DOCS := docs/setup_en.md \
	 docs/en_Pokemon\ Platinum.md
DATA := data_gen/encounters.toml \
       data_gen/items.toml \
       data_gen/locations.toml \
       data_gen/regions.toml \
       data_gen/rom_interface.toml \
       data_gen/rules.toml \
       data_gen/species.toml \
       data_gen_templates/__init__.py \
       data_gen_templates/charmap.py \
       data_gen_templates/encounters.py \
       data_gen_templates/items.py \
       data_gen_templates/locations.py \
       data_gen_templates/regions.py \
       data_gen_templates/rules.py \
       data_gen_templates/species.py \
       data_gen.py \
       data_gen_rules.py
DATA_GEN_OUT := data/__init__.py \
       data/charmap.py \
       data/encounters.py \
       data/items.py \
       data/locations.py \
       data/regions.py \
       data/rules.py \
       data/species.py

PATCHES := $(ROMS:%=patches/base_patch_%.bsdiff4)

default: pokemon_platinum.apworld

patches/base_patch_%.bsdiff4: roms/%.nds roms/target.nds
	@echo DIFF $<
	$Q./patch_gen.py $< roms/target.nds $@

data_gen: $(DATA)
	@echo DATA GEN
	$Q./data_gen.py

pokemon_platinum.apworld: data_gen $(SOURCES) #$(PATCHES)
	@echo MAKE APWORLD
	rm -f $@
	$Qmkdir -p pokemon_platinum/docs pokemon_platinum/data pokemon_platinum/patches
	$Qcp $(DATA_GEN_OUT) pokemon_platinum/data
	$Qcp $(DOCS) pokemon_platinum/docs
	$Qcp $(PATCHES) pokemon_platinum/patches
	$Qcp $(SOURCES) pokemon_platinum/
	$Qzip -r $@ pokemon_platinum
	$Qrm -r pokemon_platinum
	
