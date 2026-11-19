# Observed preparation checks

On 19 November 2026, all six CSVs were independently regenerated from the six
documented historical source files. Every output SHA256 matched the intended v4
table identity exactly. The source inputs were also hash-verified. A second path,
using only the local Afrobarometer SAV and the five published tables, produced
the same complete payload. No source microdata or Afrobarometer table were copied
into the public repository.

The final machine-readable [validation_receipt.json](validation_receipt.json)
records the preparation code SHA256 and outcomes for full and partial builds,
an exact extracted GED member, a repackaged GED archive, and expected rejections
for missing Afrobarometer input, wrong source bytes and unknown source keys.
The failure checks require that no partial output directory is installed.
Completed outputs are staged and installed by a single same-filesystem rename.

The validated environment was Python 3.12.14 on Windows, numpy 2.3.5,
pandas 3.0.1, openpyxl 3.1.5 and pyreadstat 1.3.6. The receipt contains timings,
hashes and source modes, not private input paths or respondent statistics.
We do not claim a fresh download from every provider: DataFirst files require
individual access. Current provider pages and the exact HDX resource metadata
were checked separately for identity, licensing and acquisition instructions.

Cross-platform bit identity is enforced by the output hashes but has not been
independently demonstrated on every Python/OS combination. A numerical match
with different CSV bytes is not silently accepted. The known preparation
versions are pinned; any remaining mismatch requires investigation. Rebuilding
these external tables does not rerun the competition or establish an official
TEST score for v4.
