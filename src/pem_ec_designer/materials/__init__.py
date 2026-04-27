"""Library loader: reads JSON specs into validated Pydantic objects.

Per ADR-002 D1: components are stored per-category in
library/components/{cat}.json. This loader resolves MaterialRefs
against library/materials.json and validates source IDs against
library/sources.bib.
"""

from .loader import (
    LibraryLoadError,
    Library,
    load_library,
)

__all__ = ["Library", "LibraryLoadError", "load_library"]
