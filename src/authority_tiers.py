"""
Epic 6 / Phase B / B5 — Authority tier assignment per source document.
"""

AUTHORITY_TIERS = {
    "bp1_2026-27": "primary",   # Budget Paper 1 — Budget Strategy and Outlook
    "bp2_2026-27": "primary",   # Budget Paper 2 — Budget Measures
    "budget-overview-2026-27": "summary",  # Plain-language overview document
}


def get_authority_tier(source_filename: str) -> str:
    """Return the authority tier for a source document. Raises if the
    filename isn't recognised, rather than silently defaulting — an
    untiered document should never make it into the pipeline unnoticed."""
    if source_filename not in AUTHORITY_TIERS:
        raise ValueError(
            f"No authority tier defined for '{source_filename}'. "
            f"Known documents: {list(AUTHORITY_TIERS.keys())}"
        )
    return AUTHORITY_TIERS[source_filename]