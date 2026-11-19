# Third-party notices

The repository's [MIT license](LICENSE) applies to the original submission adapters, release tools, and documentation contributed by Anton Antonov. It does not replace the licenses of vendored software, pretrained model materials, third-party packages, or datasets. The notices and license texts below remain applicable to their respective components. No model weights or respondent microdata are distributed in this repository.

## Vendored Structured Data Models

Both `solutions/r1/vendor/` and `solutions/v4/vendor/` derive from [NVIDIA Structured Data Models](https://github.com/NVIDIA/structured-data-models) at revision [`842c408fe2a8711bdf2e7cff4bfbe54266d6b940`](https://github.com/NVIDIA/structured-data-models/tree/842c408fe2a8711bdf2e7cff4bfbe54266d6b940).

Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

SDM is distributed under [Apache License 2.0](LICENSES/SDM-Apache-2.0.txt), with the additional attributions below. The original `vendor/LICENSE`, `vendor/THIRD_PARTY_LICENSES.md`, nested license files, and source-file copyright and SPDX notices are retained in each solution. [The upstream third-party notice](LICENSES/SDM-THIRD_PARTY_LICENSES.md) is also preserved verbatim; its internal relative links refer to the original vendor layout.

The historical r1 and v4 ZIPs contain identical vendor trees. Comparing every bundled vendor file against the pinned upstream revision found one changed upstream source file: `sdm/models/base.py`. Its cache-placement condition adds `and getattr(self, "_offload_cache", True)` so the adapter can keep estimator caches on CUDA. `vendor/REVISION` records the source revision and is an added provenance file. The released copies of `base.py` carry a prominent modification notice. This added comment changes the release file bytes without changing executable behavior; the original competition ZIP hash is provenance, not the hash of a rebuilt public ZIP.

## Components within the vendor tree

Paths in this table are relative to either solution's `vendor/` directory. These attributions apply even where a retained architecture is not selected by the submitted predictor.

| Component and copyright | Bundled locations | License text |
| --- | --- | --- |
| [TabICLv2](https://github.com/soda-inria/tabicl), Copyright (c) 2025, Soda team @ Inria | `sdm/models/tabiclv2/`; derived components in `sdm/models/kumo/relational/` and `sdm/nn/scaling.py` | [BSD 3-Clause](LICENSES/TabICLv2-BSD-3-Clause.txt), plus the retained [Kumo-Relational notice](LICENSES/Kumo-Relational-NOTICE.txt) |
| [TabFM](https://github.com/google-research/tabfm), Copyright 2026 Google LLC | `sdm/models/tabfm/` and derived portions of `sdm/nn/glu.py` | [Apache 2.0 for code](LICENSES/TabFM-code-Apache-2.0.txt) |
| [TimesFM 3.0](https://github.com/google-research/timesfm), Copyright 2026 Google LLC | `sdm/models/timesfm3/` | [Apache 2.0 for code](LICENSES/TimesFM3-code-Apache-2.0.txt) |
| [TabPFN Extensions](https://github.com/PriorLabs/tabpfn-extensions), Copyright 2025 Prior Labs GmbH | Derived portions of `sdm/models/ecoc.py` | [Apache 2.0](LICENSES/TabPFN-Extensions-Apache-2.0.txt) |

NVIDIA's copyright notices and Apache license also apply to its contributions to these files. The retained original notices identify the contributions of their respective authors; they must not be removed or replaced with the repository's MIT header.

The upstream distribution also includes [PyTorch's complete copyright and BSD license notice](LICENSES/PyTorch-BSD-3-Clause.txt) for its contribution-guide attribution, and the [Contributor Covenant MIT notice](LICENSES/Contributor-Covenant-MIT.txt), Copyright (c) 2014 Coraline Ada Ehmke. These upstream notices are retained although `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` themselves are not included in the submission snapshots. The PyTorch notice includes its original PyTorch/Caffe2 copyright list; this summary does not replace it.

## Pretrained model materials

Both predictors select only [NVIDIA Kumo-Tabular](https://huggingface.co/nvidia/Kumo-Tabular), `large/classifier.pt`, at model repository revision `3520742f7f3b937a2751266cea22d7fb6686882c`. The checkpoint has SHA-256 `cc21484316949641cc3d65a7bb6c36cdea854cc569435755ff23b850018ec613` and size 854,850,034 bytes. Each solution retains its `checkpoint_manifest.json`.

Kumo model materials are licensed under [OpenMDW 1.1](LICENSES/Kumo-Tabular-OpenMDW-1.1.txt), Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. The model license is separate from the Apache license for SDM and the MIT license for this repository. Redistribution of model materials requires retaining the OpenMDW agreement and applicable notices of origin. This repository supplies download metadata rather than the checkpoint.

The retained TabFM and TimesFM implementations are Apache-licensed code. Their pretrained weights have separate non-commercial licenses; code-license terms do not grant rights to those weights. Neither predictor downloads, loads, or distributes TabFM or TimesFM weights. The [historical TabFM weights-license copy](LICENSES/TabFM-weights-Non-Commercial-v1.0.txt) is retained for provenance only. Its section 3(b) prohibits distribution of the model or derivatives under that license, so it must not be treated as a redistribution permission. See the official [TabFM model license](https://huggingface.co/google/tabfm-1.0.0-pytorch/blob/main/LICENSE) and [TimesFM model license](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE) before any separate use.

## Dependencies and data

`requirements.txt` files declare separately installed packages. Their source, wheels, and CUDA libraries are not bundled here and retain their own licenses. The bundled PyTorch attribution above concerns SDM's inherited notice; it does not relicense an installed PyTorch or NVIDIA CUDA distribution.

No dataset license or permission to redistribute respondent records is granted by this repository's MIT license. Some aggregate tables are included under their providers' terms, as documented in [data/SOURCE_TERMS.md](data/SOURCE_TERMS.md). Other sources, including any artifacts whose redistribution permission has not been established, remain local and must be supplied separately when needed. Consult the release's data documentation and the original data providers' terms before preparing or redistributing those artifacts.

[LICENSES/SOURCE_MANIFEST.json](LICENSES/SOURCE_MANIFEST.json) records the exact copied license and notice files, their SHA-256 hashes, the original archive entries, and upstream source URLs. The vendored license texts were copied byte-for-byte from the historical r1 ZIP and agree with those in v4. The pinned upstream SDM license and third-party notice and the pinned Kumo license were also verified against their official primary-source URLs on 19 November 2026.
