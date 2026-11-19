# External data for the intended v4 variant

This directory supplies five cleared derived CSV tables and a local preparation
tool for the sixth, Afrobarometer. The historical v4 method uses exactly six
tables and 23 numerical context features. The competition upload was **r1**;
these external features belong to the intended v4 variant, not its reported
official TEST score.

Read [SOURCE_TERMS.md](SOURCE_TERMS.md) for provider terms and attribution and
[aggregates/README.md](aggregates/README.md) for the included data. Raw microdata,
Afrobarometer numerical aggregates, and the historical source-audit controls are
not distributed. The repository's software licence does not license third-party
data. Keep generated full v4 bundles private unless all applicable redistribution
rights, including Afrobarometer derivative rights, have been established.

## Prepare using the published tables

Use a Python 3.12 environment; the validated preparation versions are pinned in
[requirements-prepare.txt](requirements-prepare.txt). A suitable conda environment
name is `antonov-simulacra-data`:

```sh
conda create -n antonov-simulacra-data python=3.12 pip
conda activate antonov-simulacra-data
python -m pip install -r data/requirements-prepare.txt
```

Run the remaining commands from the repository root. Obtain the documented
Afrobarometer Round 9 SAV from its provider. The current download is a ZIP; extract
the SAV and do not resave or export it. Copy `data/inputs.example.json` to
`data/inputs.local.json` and set `afro` to your local SAV. Relative paths resolve
beside the input JSON; absolute paths also work. Filename spelling is not used
as proof of identity: the bytes must match the manifest.

```sh
python data/prepare.py --inputs data/inputs.local.json --output data/generated
python tools/build_submission.py v4 --external-data data/generated --output build/v4.zip
```

The first command reads your local Afrobarometer source, recomputes its table,
verifies and copies the other five published tables, and checks every output
against the six historical CSV SHA256 hashes. It installs `manifest.json`, six
CSV files and `preparation.json` only after all checks pass. The output directory
must be new or empty. Preparation performs no network requests, downloads, model
inference, or joins to benchmark responses. Model runtime uses the prepared
tables and does not access raw data or download data.

`data/generated/`, `data/raw-inputs/` and `data/inputs.local.json` are ignored by
Git. These exclusions do not grant publication rights for `build/v4.zip` or any
other generated archive: a complete v4 archive contains the excluded Afrobarometer
derivative. Do not attach it to a public release on the basis of this repository's
code licence.

## Rebuild every table from your own downloads

Use `inputs.full.example.json` as the local input JSON instead. Any supplied source
is rebuilt; any omitted source uses its verified published aggregate, if one is
available. Afrobarometer has no published table and always needs a local input.
An arbitrary subset of the other five sources can therefore be rebuilt.

The input contract, column names, sheets/archive members, source versions,
byte lengths, raw-file hashes, extracted-member hashes and output hashes are in
[source_manifest.json](source_manifest.json). Obtain the files independently:

| Key | Exact source and acquisition | Required local input |
| --- | --- | --- |
| `afro` | [Afrobarometer merged Round 9, 39 countries](https://www.afrobarometer.org/survey-resource/merged-round-9-data-39-countries-2023/), update 4 June 2025; use Download SAV and extract if zipped | Unmodified `R9.Merge_39ctry.20Nov23.final_.release_Updated.4Jun25-3.sav` |
| `wgm` | [Wellcome Global Monitor 2018](https://wellcome.org/insights/reports/wellcome-global-monitor-2018), Downloads, Appendix D | [All-country dataset/crosstabs XLSX](https://wellcome.org/sites/default/files/wgm2018-dataset-crosstabs-all-countries.xlsx), containing `Data dictionary` and `Full dataset` |
| `palms` | [DataFirst PALMS v4 catalog](https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/434), Get Microdata; use your own registered access and the main Stata file for 1993–2025 | `palmsv4.zip` with `palmsv4.dta`, or the exact extracted DTA |
| `pases` | [DataFirst PASES v1.1 catalog](https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/1083), Get Microdata; use your own registered access and the main Stata file for 1995–2024 | `pases-1995-2024-v1.1-stata.zip` with `pases-1995-2024-v1.1-stata/pasesv1.1.dta`, or the exact extracted DTA |
| `hno` | [OCHA Syria Humanitarian Needs on HDX](https://data.humdata.org/dataset/syrian-arab-republic-humanitarian-needs), resource `0bc1b237-862c-47f9-b751-443d8ffa9bee`, named `syr_hpc_needs_2024.xlsx` in the catalog | [PiN/severity workbook, 2024-04-01](https://data.humdata.org/dataset/cfd515f3-e45c-4c6b-a0f4-1a517f0b726f/resource/0bc1b237-862c-47f9-b751-443d8ffa9bee/download/pin_severity_hno_2024_20240401.xlsx) |
| `ged` | [UCDP GED Global v26.1](https://ucdp.uu.se/downloads/), CSV | [ged261-csv.zip](https://ucdp.uu.se/downloads/ged/ged261-csv.zip) with `GEDEvent_v26_1.csv`, or the exact extracted CSV |

Download filenames and outer ZIP packaging may vary. PALMS, PASES and GED can be
provided as a differently compressed ZIP containing the exact documented member,
or directly as that member. Both its byte length and SHA256 must match the manifest.
An archive with a different member path can be extracted by the user and supplied
as the DTA/CSV. No private historical wrapper archive is necessary. For SAV and XLSX,
only the exact file bytes are certified; the current Afrobarometer ZIP must first
be extracted. Different substantive releases, resaved workbooks, or matching column
names alone are not accepted. If a provider no longer supplies the pinned version,
request that version from the provider; this tool cannot promise equivalence to an
unverified replacement. Do not change expected hashes merely to make it run.

Preparation uses approximately 2 GB of temporary disk for the two Stata inputs
when both labour sources are rebuilt. Temporary extracted files are removed after
the run. Local output receipts contain file hashes and package versions, with no
absolute input paths or response-level data.

## Transformation and verification

The public tool adapts the historical aggregate builder: survey proportions retain
the same denominator rules, positive finite weights, grouping order, float64
sums and CSV serialization. Effective sample size is `(sum w)^2 / sum(w^2)`;
the runtime uses the same fallback groups and thresholds (50 for Afrobarometer/WGM,
100 for PALMS/PASES). PALMS selects wave 92, PASES year 2024. HNO takes unweighted
governorate means of valid subdistrict severity codes. GED counts mapped Syria
events with equal parsed start/end dates in 2024 and January–April 2025, then applies
`log1p`. These are contextual features, not linked respondent records or benchmark
target labels. HNO means are ordinal-code summaries; GED equal dates do not prove
day-level temporal precision.

The [public runtime manifest](historical_v4_manifest.public.json) preserves feature
definitions and expected table identities. Historical audit controls, private source
paths and unnecessary feature-group counts have been removed; it is not the original
manifest byte stream, so an assembled public v4 archive is not claimed to have the
historical v4 ZIP hash. Its six CSV files must still be byte-identical.

See [VALIDATION.md](VALIDATION.md) for observed checks and limitations.
