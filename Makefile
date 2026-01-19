
.PHONY: data_gen update_apnds

Q ?= @

ROMS := us_rev0 us_rev1
SOURCES := __init__.py \
	 client.py \
	 items.py \
	 locations.py \
	 options.py \
	 regions.py \
	 rules.py \
	 LICENSE
ROM_SOURCES := rom/__init__.py \
	rom/itemdata.py
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
APNDS_VERSION := 0.1.2
APNDS_FILES := apnds/LICENSE \
	apnds/__init__.py \
	apnds/lz.py \
	apnds/narc.py \
	apnds/rom.py

PATCHES := $(ROMS:%=patches/base_patch_%.bsdiff4)

default: pokemon_platinum.apworld

patches/base_patch_%.bsdiff4: roms/%.nds roms/target.nds
	@echo DIFF $<
	$Q./patch_gen.py $< roms/target.nds $@

data_gen: $(DATA)
	@echo DATA GEN
	$Q./data_gen.py

update_apnds:
	@if [ -d "apnds" ] && [ -f "apnds/version" ] && [ "`cat apnds/version`" = "$(APNDS_VERSION)" ]; then \
	    :; \
	else \
	    echo UDPATE APNDS; \
	    curl -LSso apnds.tar.gz https://github.com/ljtpetersen/apnds/releases/download/v$(APNDS_VERSION)/apnds.tar.gz && \
	    rm -rf apnds && \
	    tar xzf apnds.tar.gz && \
	    rm apnds.tar.gz && \
	    echo $(APNDS_VERSION) >apnds/version; \
	fi

pokemon_platinum.apworld: data_gen $(SOURCES) update_apnds $(PATCHES)
	@echo MAKE APWORLD
	$Qcd ../..; python Launcher.py "Build APWorlds" "Pokemon Platinum"
	$Qcp ../../build/apworlds/pokemon_platinum.apworld .
