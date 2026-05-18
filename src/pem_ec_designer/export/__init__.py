"""Export layer — turn an in-memory design point into shareable files.

Two formats land in v1.0:
  - `.csv`  V–I sweep + loss breakdown (csv_export.write_polarisation_csv)
  - `.bib`  Subset of library/sources.bib containing only the keys cited
            by the current stack (bibtex_export.write_bibtex_subset)

STEP / PDF land in C+ Teil 2b. Layer rule: this package may import
physics/assembly value objects but NEVER Qt.
"""
