# Submission source snapshots

`r1/` contains the code of the submitted full-context Kumo Large solution. Its historical ZIP SHA256 is `0594c4c57fa879a87638741ccdb955449e02ababfd34d0e6e8fa85c02c84af2d`. `v4/` contains the later audited external-feature and all-target calibration variant. Its historical ZIP SHA256 is `76f74bf8267b84dea155fb0771761df8d6633b8a1e596643457cc4055a5817d6`. The report identifies which scores belong to the submitted artifact; v4 has no measured real-data quality result.

Both source trees add a prominent modification notice to `vendor/sdm/models/base.py`. That comment is the only change to executable Python source. In v4, the external-data manifest also omits non-runtime audit information and derived control counts. The runtime source directory omits its six aggregate CSVs. The cleared tables and preparation instructions are in `data/`; follow `data/README.md` to assemble the complete set locally under the providers' terms. Model weights and benchmark respondent records are not included.

Each `release_manifest.json` records the original member order, ZIP metadata, historical file hashes, current public source hashes, and omitted assets. `python tools/verify_sources.py --historical-r1` verifies both public source trees and reconstructs the original r1 ZIP **in memory only** to check its SHA256. It does not emit the historical archive, whose modified vendored file lacked the new explicit notice. Historical reconstruction also depends on compatible DEFLATE output; the verification fails explicitly if the source bytes match but the compression library differs.

Public ZIPs use sorted names, fixed timestamps, fixed permissions and uncompressed ZIP entries for deterministic output across compression-library versions. They include the public licenses and provenance, so their archive hashes differ from the competition originals. The builder verifies all input hashes, accepts an identical existing output, and refuses to replace different contents. It creates a complete ZIP atomically with an exclusive rename on Windows or a hard link on POSIX filesystems.

```sh
python tools/verify_sources.py --historical-r1
python tools/build_submission.py r1 --output build/r1.zip
# After locally preparing all six aggregate CSVs:
python tools/build_submission.py v4 --external-data data/generated --output build/v4.zip
```

Run the organizer's smoke checker with the supplied `tools/check_submission.py` wrapper and a prepared Hugging Face hub cache. Both execution wrappers preserve the scheduler's `CUDA_VISIBLE_DEVICES` when `--gpu` is omitted; an explicit `--gpu` overrides it, and `--cpu` hides CUDA devices. The checker validates the submission interface on synthetic rows; it does not reproduce a hidden-test score or impose the full competition sandbox. `tools/run_prediction.py --help` describes direct prediction on a supplied CSV/schema pair; it is also an inference call, not a scoring script. Its CSV reader preserves string labels, including `NA`, `NULL` and leading zeros, and treats blank cells as missing prediction targets.
