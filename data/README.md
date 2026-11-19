# Data for the survey-context model

The variant uses 23 features from six sources. Five tables are available in [aggregates](aggregates/). The sixth is built locally from Afrobarometer Round 9. The submitted competition model runs without any of these tables.

| Instrument | Sources | What they add |
| --- | --- | --- |
| UNICEF | Wellcome Global Monitor, Afrobarometer | Demographic-group estimates of vaccine attitudes and trust |
| World Bank | PALMS, PASES | Job-search duration and labour-market estimates for South Africa |
| UNHCR | Syria Humanitarian Needs, UCDP | Humanitarian needs and conflict counts by governorate of origin |

## Prepare the survey-context model

1. Download the June 2025 update of [Afrobarometer Round 9](https://www.afrobarometer.org/survey-resource/merged-round-9-data-39-countries-2023/). Extract the original SPSS file.
2. Copy `data/inputs.example.json` to `data/inputs.local.json` and enter the path to your SPSS file. Relative paths start at the directory containing the JSON file.
3. In a dedicated Python 3.12 environment, run the following commands from the repository root.

```sh
python -m pip install -r data/requirements-prepare.txt
python data/prepare.py --inputs data/inputs.local.json --output data/generated
python tools/build_submission.py survey-context --external-data data/generated --output build/survey-context.zip
```

The script computes the Afrobarometer table, verifies all six tables, and installs the result in a new or empty output directory. Keep the assembled archive local because it contains the Afrobarometer-derived table. See the [source terms and attribution](SOURCE_TERMS.md).

## Rebuild all six tables

Use `data/inputs.full.example.json` to specify your own copies of all six sources. The [source inventory](source_manifest.json) identifies the precise releases, filenames, workbook sheets and required columns. PALMS, PASES and UCDP accept the original archive or its unmodified data member. Allow about 2 GB of temporary disk space for the labour datasets.

Survey estimates use source weights and fall back to broader demographic groups when a group is small. The regional tables summarize Syrian governorates of origin. See the [feature definitions](feature_definitions.json) and [preparation checks](VALIDATION.md).
