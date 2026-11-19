# Run the models

The submitted model needs the survey inputs and the Kumo Large checkpoint. The survey-context model also uses six aggregate tables. Five accompany this repository. The [data guide](../data/README.md) explains how to prepare the Afrobarometer table locally and build the survey-context package.

## Check a model

Use a separate Linux environment for inference. The competition rehearsal used Python 3.12, one H100 GPU and eight CPU threads. Download the [tested organizer starter kit](https://github.com/SituatedEvals/public/tree/aa03186f8f083c7785a1a566c802c2077925e265) into `build/starter-kit`, then run:

```sh
python -m pip install -r solutions/submitted/requirements.txt
export HF_HUB_CACHE="$PWD/.model-cache"
python tools/prepare_weights.py --cache-dir "$HF_HUB_CACHE"
python tools/check_submission.py --archive build/submitted.zip \
  --checker build/starter-kit/tools/check_submission_zip.py --hf-cache "$HF_HUB_CACHE"
```

Weight preparation downloads the frozen [Kumo Large checkpoint](https://huggingface.co/nvidia/Kumo-Tabular), approximately 855 MB. It can reuse a downloaded file with `--checkpoint /path/to/classifier.pt`. The check uses the prepared cache and preserves the scheduler's GPU selection; `--cpu` is also available. To check the survey-context variant, change the archive path to `build/survey-context.zip` after preparing its data.

The check validates probability outputs on a small synthetic questionnaire. The starter kit's `make_sandbox.py` and `score.py` support full synthetic surveys. Official test scores require the organizers' protected data and evaluation infrastructure.

Run the commands from the repository root after building the relevant package. See the [competition entry](../README.md), [third-party licences](../THIRD_PARTY_NOTICES.md), and [data terms](../data/SOURCE_TERMS.md).
