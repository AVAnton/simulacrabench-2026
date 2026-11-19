# Predicting survey responses with Kumo Large

SimulacraBench asks for a probability distribution over each respondent's hidden survey answers. We used Kumo Large to learn from the visible responses to each question and calibrated its confidence on held-out respondents. Team **aa_FusionBrain** placed fifth in the 19 November standings. [Competition](https://simulacrabench.org/).

| Model | Inputs | Official result |
| --- | --- | --- |
| [Submitted model](solutions/submitted/) | The respondent's visible survey profile | Overall Skill **0.49** |
| [Survey-context variant](solutions/survey-context/) | The same profile plus 23 features describing attitudes, labour markets and regional conditions | Experimental, no test submission |

The submitted model scored **0.88** on UNHCR, **0.34** on UNICEF and **0.24** on the World Bank survey.

## Reproduce the submission

From the repository root, run this command with Python 3.12.

```sh
python tools/build_submission.py submitted --output build/submitted.zip
```

The [execution guide](solutions/README.md) covers weights and the organizer's synthetic check. To run the survey-context model, start with the [data preparation guide](data/README.md).

Anton Antonov, FusionBrain Laboratory. The original code is available under [MIT](LICENSE). [Third-party software and model licences](THIRD_PARTY_NOTICES.md) · [Dataset terms and attribution](data/SOURCE_TERMS.md).
