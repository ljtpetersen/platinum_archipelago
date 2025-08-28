# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.0.2 - TBD
## Added
* Starting inventory support.
* Item groups.
## Fixed
* Crashes when giving multiple bag items (like `Rare Candy x15`) with `nothing` item receiving notification option.
* Crashes when giving multiple Pokétches with `jingle` and `nothing` item receiving notification options.
* Generation error when using `poketch_apps = false`.
* Issues running data generation with Python version < 3.12.
* Hardlock when obtaining the Pokétch from a local location.
* Random text frame is now random.
* Added connection from Route 207 to Route 207 South.
# Changed
* Game options now use the default value if there is no corresponding entry in the YAML.
* Game options now raise exceptions if invalid values are entered.

## [0.0.1] - 2025-08-26
The first release of this project.

[0.0.1]: https://github.com/ljtpetersen/platinum_archipelago/releases/tag/v0.0.1
