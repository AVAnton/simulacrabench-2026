# Data preparation checks

We rebuilt all six tables from the original source files. A second run started with the five published tables and only the original Afrobarometer file. Both produced the same six tables used by the survey-context model.

The preparation script also accepted an unchanged UCDP data file supplied separately or in a repackaged archive. Missing inputs, unexpected source versions and unknown keys were rejected before any output was installed. The [verification record](validation_receipt.json) gives the tested environment and individual results.
