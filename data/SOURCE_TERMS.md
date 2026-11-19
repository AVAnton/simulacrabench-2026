# Source terms and attribution

Checked against the official provider pages/API on 19 November 2026. The five
included CSVs are derived numerical tables, not source microdata. Their source
terms are separate from the repository's software licence; no third-party data
are relicensed under MIT. Changes made by this project are described below and
in `prepare.py`. The providers have not endorsed this method or its interpretations.

| Source | Verified terms | Release decision |
| --- | --- | --- |
| Afrobarometer Round 9 | Custom data-use policy; copyright retained; source citation required. No explicit grant for redistribution of these machine-readable derived tables was established. | No raw data, `afro.csv`, or numerical Afrobarometer audit controls are included. Lawful local preparation is supported. |
| Wellcome Global Monitor 2018 | The official report's copyright notice expressly permits redistribution of data/text under CC BY with author/source credit. The report does not give a licence version; Wellcome's general website terms specify CC BY 4.0 by default. | Include `wgm.csv` with attribution and modification notice. |
| PALMS 1993–2025 v4 | Its exact DataFirst catalog labels the data CC BY (attribution only), without a version number. | Include `palms.csv` under that source notice, with required citation. |
| PASES 1995–2024 v1.1 | Its exact DataFirst catalog labels the data CC BY (attribution only), without a version number. | Include `pases.csv` under that source notice, with required citation. |
| Syria HNO 2024 | Official HDX CKAN metadata for the exact workbook's dataset gives `license_id=cc-by`, title `Creative Commons Attribution International (CC BY)` and a licence URL. It does not state a version number. | Include `hno.csv` with OCHA/Humanitarian partners attribution. |
| UCDP GED Global v26.1 | The official UCDP download center expressly permits use and redistribution under CC BY 4.0 and requests the listed dataset/publication citations. | Include `ged.csv` with those citations and modification notice. |

CC BY licences permit sharing and adaptation subject to their conditions. For
PALMS/PASES/HNO this release preserves the publisher's label without inventing a
version. DataFirst's general portal terms contain generic microdata conditions
alongside source-specific access rules; the affirmative evidence used here is the
CC BY notice in each exact catalog entry. Follow the conditions presented when
obtaining your own source files; access registration does not transfer another
person's account or permissions.

## Afrobarometer

Source: [merged Round 9, 39 countries, June 2025 update](https://www.afrobarometer.org/survey-resource/merged-round-9-data-39-countries-2023/).
Terms: [Data usage and access policy](https://www.afrobarometer.org/data/data-usage-and-access-policy/).
The provider requires bibliographic acknowledgment and asks users to send copies
of publications. No communication has been sent by this release process.

Attribution for a permitted use: Afrobarometer Data, Kenya, Mali, Nigeria and Zambia,
Round 9, 2021–2022 fieldwork, available at [Afrobarometer](https://www.afrobarometer.org).
Local changes: selected-country weighted vaccine/trust proportions by documented
demographic groups. Publicly distributing the full survey-context archive would also
distribute this excluded derivative; do not do so without established permission.

## Wellcome Global Monitor

Attribution: Gallup (2019), *Wellcome Global Monitor – First Wave Findings*;
copyright Wellcome. [Source and Appendix D](https://wellcome.org/insights/reports/wellcome-global-monitor-2018).
Evidence: [official report, copyright notice on PDF page 2](https://cms.wellcome.org/sites/default/files/wellcome-global-monitor-2018.pdf#page=2)
and [Wellcome website terms](https://wellcome.org/about-us/our-people/governance/privacy-and-terms).
The website's stated default is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Changes: selected adults in ten countries; seven weighted vaccine, health-trust
and science/religion proportions with prescribed demographic fallbacks. No report
photographs or other excluded images are included.

Collection-level supporting attribution: Wellcome Trust and Gallup Organization Ltd,
*Wellcome Global Monitor, 2018*, 2nd edition (2019), UK Data Service,
[doi:10.5255/UKDA-SN-8466-2](https://doi.org/10.5255/UKDA-SN-8466-2).
The [UK Data Service catalog](https://datacatalogue.ukdataservice.ac.uk/studies/study/8466)
lists CC BY 4.0 for that collection. This supports the collection attribution;
it is not substituted for the exact Appendix D workbook's identity or Wellcome's
source-specific copyright notice above.

## DataFirst labour series

PALMS attribution: Andrew Kerr, David Lam and Martin Wittenberg; *Post-Apartheid
Labour Market Series 1993–2025*, version 4; DataFirst, Cape Town, producer and
distributor, 2025. [DOI: 10.25828/gtr1-8r20](https://doi.org/10.25828/gtr1-8r20).
The [exact catalog's Access policy](https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/434)
provides the CC BY notice and citation. Changes: wave 92 (2025 Q2), ages 15–64,
three weighted elapsed-job-search shares among eligible unemployed respondents.

PASES attribution: Andrew Kerr, Amy Thornton and Martin Wittenberg; *Post-Apartheid
Socio-Economic Series 1995–2024*, version 1.1; DataFirst, Cape Town, producer and
distributor, 2026. [DOI: 10.25828/49GK-P872](https://doi.org/10.25828/49GK-P872).
The [exact catalog's Access policy](https://www.datafirst.uct.ac.za/dataportal/index.php/catalog/1083)
provides the CC BY notice and citation. Changes: year 2024, ages 15–64; three weighted
unemployment, active-search and paid-work proportions. These are separate constructs
with separate denominators, not probabilities of future hiring.

Statistics South Africa supplied underlying surveys for these harmonised series;
the PALMS series also includes the 1993 SALDRU survey. Obtain each series through
DataFirst's own Get Microdata process. [General portal terms](https://www.datafirst.uct.ac.za/dataportal/index.php/terms-of-use)
are linked for access-context completeness; the dataset-specific notices above
are the release evidence for these derived tables.

The portal's generic microdata conditions describe statistical/scientific research
and generating or reporting aggregate information, prohibit identifying respondents,
and restrict redistribution of supplied microdata/material without agreement.
This release includes aggregate statistical outputs only. Users obtaining source
files must also comply with the access conditions accepted for their own download;
the dataset-specific CC BY notices are not represented as permission to disregard
those conditions or release respondent records.

## OCHA Syria HNO

Attribution: OCHA on behalf of the Humanitarian Country Team and partners,
*Syrian Arab Republic: Humanitarian Needs*, 2024 PiN/severity workbook, revision
1 April 2024, distributed through [HDX](https://data.humdata.org/dataset/syrian-arab-republic-humanitarian-needs).
The [official package_show API](https://data.humdata.org/api/3/action/package_show?id=syrian-arab-republic-humanitarian-needs)
identifies the exact resource `0bc1b237-862c-47f9-b751-443d8ffa9bee`, download filename
`pin_severity_hno_2024_20240401.xlsx`, size 78,280 bytes, and the dataset's CC BY
notice. The published licence link is [CC BY via Open Definition](http://www.opendefinition.org/licenses/cc-by).
Changes: unweighted means of valid protection, mine-action and education severity
codes by Syrian governorate. These are summaries of administrative subdistrict
assessments, not individual household records or population-weighted estimates.

## UCDP GED

Attribution: Uppsala Conflict Data Program, UCDP Georeferenced Event Dataset,
Global version 26.1. [Download center and source terms](https://ucdp.uu.se/downloads/),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Required publications:
Shawn Davies, Therése Pettersson and Magnus Öberg (2026), *Organized violence
1989–2025, and violent political protests*, Journal of Peace Research,
[doi:10.1093/jopres/xjag046](https://doi.org/10.1093/jopres/xjag046);
Ralph Sundberg and Erik Melander (2013), *Introducing the UCDP Georeferenced Event
Dataset*, Journal of Peace Research 50(4). UCDP is part of DEMSCORE, supported by
Swedish Research Council grant 2021-00162, as acknowledged on the source page.
Changes: mapped Syrian governorate counts for two windows, restricted to records
with equal parsed start/end dates; `log1p` transform. No fatality estimates are used.

## Sources outside the survey-context model

VCI annual files, VASyR workbooks, Arab Barometer and the Harvard Syrian-refugee
proxy data are not inputs to these six tables. No rights from those sources are
assumed or transferred to this release. A permissive licence for an article,
basemap, or portal software is not treated as a licence for an unrelated dataset.
