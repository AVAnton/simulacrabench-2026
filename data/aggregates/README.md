# Published derived tables

These five tables are byte-identical to their historical intended-v4 counterparts.
They contain derived context statistics only. Their third-party source terms and
required attribution are in [SOURCE_TERMS.md](../SOURCE_TERMS.md), which accompanies
these data; the repository's MIT code licence does not cover them. Preserve those
attributions, source/terms links and modification notices when redistributing.
The compact [ATTRIBUTION.md](ATTRIBUTION.md) is co-located with the CSVs for this purpose.

| File | Source / version | Terms | Rows | Changes |
| --- | --- | --- | ---: | --- |
| `wgm.csv` | Gallup / Wellcome Global Monitor 2018 | CC BY; report unspecified version, website default 4.0 | 890 | Seven weighted demographic context proportions |
| `palms.csv` | Kerr, Lam, Wittenberg / DataFirst PALMS v4 (2025) | CC BY, source does not specify version | 63 | Three weighted search-duration proportions |
| `pases.csv` | Kerr, Thornton, Wittenberg / DataFirst PASES v1.1 (2026) | CC BY, source does not specify version | 63 | Three weighted labour-market proportions |
| `hno.csv` | OCHA / Humanitarian partners, Syria HNO 2024, 2024-04-01 workbook | HDX CC BY, metadata does not specify version | 42 | Three unweighted severity-code means by governorate |
| `ged.csv` | UCDP GED Global v26.1 | CC BY 4.0 | 28 | Two time-window counts by governorate, transformed with `log1p` |

SHA256 identities and the precise source files are in
[source_manifest.json](../source_manifest.json). `afro.csv` is deliberately absent.
Use [the preparation instructions](../README.md) with your own lawfully obtained
Afrobarometer SAV to create a complete private v4 data folder. The combined output
has different redistribution status from the five files in this directory.
