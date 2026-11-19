# Predicting survey responses with Kumo Large

Two SimulacraBench 2026 predictors from team **aa_FusionBrain** (Anton Antonov, FusionBrain Laboratory). Both condition one frozen Kumo Large classifier on the visible training responses to each survey question, calibrate answer probabilities on a training holdout, and apply questionnaire skip rules.

| Solution | Inputs and calibration | Official TEST |
| --- | --- | --- |
| [r1](solutions/r1/) | Within-survey covariates and interactions, one selected temperature per instrument | Submission 1053698, overall Skill **0.49** |
| [v4](solutions/v4/) | Adds 23 external demographic and regional features, revises a schooling skip rule, and can fit separate temperatures for skips and substantive answers | Experimental, no TEST submission |

The r1 instrument scores displayed by Codabench were 0.34 for UNICEF, 0.24 for the World Bank and 0.88 for UNHCR. The team recorded fifth place on 19 November 2026. The closed evaluation runs on the organizers' infrastructure. The public checks below use synthetic inputs. [Competition and evaluation protocol](https://simulacrabench.org/).

## Reproduce r1

Run the following commands from the repository root on Linux. Packaging and source verification use the Python 3.12 standard library.

```sh
python tools/verify_sources.py --solution r1 --historical-r1
python tools/build_submission.py r1 --output build/r1.zip
```

The first command reconstructs the original archive in memory and verifies its SHA-256, `0594c4c57fa879a87638741ccdb955449e02ababfd34d0e6e8fa85c02c84af2d`. The second creates a deterministic ZIP with the same predictor and the licensing notices for this release. Historical archive identity and release package identity are recorded separately.

## Prepare v4 from source data

[Data preparation and provider terms](data/README.md) identifies the exact inputs, citations and licences. For the shortest reproduction, obtain the specified Afrobarometer Round 9 file from its provider and set its path in a local copy of `data/inputs.example.json`. The other five derived tables are included with their source attributions. `data/inputs.full.example.json` describes a complete rebuild from all six provider files. Use a separate Python environment for data preparation.

```sh
python -m pip install -r data/requirements-prepare.txt
python data/prepare.py --inputs data/inputs.local.json --output data/generated
python tools/build_submission.py v4 --external-data data/generated --output build/v4.zip
```

The preparation script checks each derived table against the hashes used by the historical v4 predictor. The ZIP produced by the second command embeds the tables for offline inference. Keep it in the local build directory. Public redistribution of the Afrobarometer-derived table has not been established. The public repository supplies the preparation code and source references.

## Run the organizer's smoke check

Install the runtime requirements for the selected solution in a separate Linux environment. The frozen hardware rehearsal used Python 3.12, one H100 80 GB and eight CPU threads. For local validation the weight preparation step downloads one pinned 855 MB checkpoint. It can also reuse a local copy with `--checkpoint /path/to/large/classifier.pt`.

```sh
python -m pip install -r solutions/r1/requirements.txt
export HF_HUB_CACHE="$PWD/.model-cache"
python tools/prepare_weights.py --cache-dir "$HF_HUB_CACHE"
git clone https://github.com/SituatedEvals/public.git build/starter-kit
git -C build/starter-kit checkout aa03186f8f083c7785a1a566c802c2077925e265
HF_HUB_OFFLINE=1 python build/starter-kit/tools/check_submission_zip.py build/r1.zip
HF_HUB_OFFLINE=1 python build/starter-kit/tools/check_submission_zip.py build/v4.zip
```

Run the v4 command after preparing its data and ZIP. The organizer's check imports the predictor and validates probability vectors on a synthetic questionnaire. The protected test data and official scores can only be reproduced by the organizers. Both solutions load `nvidia/Kumo-Tabular`, file `large/classifier.pt`, revision `3520742f7f3b937a2751266cea22d7fb6686882c`. The runtime verifies the checkpoint digest and works from the prepared cache. [Model card](https://huggingface.co/nvidia/Kumo-Tabular).


## Score a full synthetic survey

The public starter kit can also generate complete native-shaped instruments and score a predictor. Its scorer accepts one schema per invocation. Each call creates a fresh environment, installs the solution requirements and evaluates one instrument. Local synthetic scores describe the generated survey. For a phase-2 example with r1:

```sh
mkdir -p build/scores
for name in unicef world_bank unhcr; do
  python build/starter-kit/make_sandbox.py --config build/starter-kit/config.yml \
    --schema "build/starter-kit/data/$name.json" --out "build/synthetic/$name" --seed 0
  python build/starter-kit/score.py --config build/starter-kit/config.yml \
    --submission solutions/r1 --schema "build/starter-kit/data/$name.json" \
    --data "build/synthetic/$name" --phase 2 --seed 0 --log "build/scores/r1-$name.json"
done
```

For v4, extract the locally built `build/v4.zip` to `build/v4-solution` and pass that directory to `--submission`. Use the prepared model cache and the solution runtime for both versions. The scorer may need network access during dependency installation.

## Licensing

The team's original adapters, preparation scripts and release tools are available under the [MIT license](LICENSE). MIT allows research and commercial reuse subject to its notice requirement. The competition requires permission for non-commercial research reproduction and OpenReview accepts MIT for submitted code. [Competition rules](https://simulacrabench.org/) · [OpenReview invitation](https://api2.openreview.net/invitations?id=NeurIPS.cc/2026/Competition/SimulacraBench/-/Submission).

The included third-party software retains its own licences and notices. SDM uses Apache-2.0 with additional upstream attributions. The separately obtained Kumo weights use OpenMDW 1.1. The six external data sources retain their provider terms. [Third-party notices](THIRD_PARTY_NOTICES.md) · [Data source terms](data/SOURCE_TERMS.md).
