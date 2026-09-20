"""
Epic 6 / Phase B / B5 — Authority tier assignment per source document.
"""

AUTHORITY_TIERS = {
    "Strategy and Outlook_2026-27": "primary",          # Budget Paper 1
    "Budget Measures_2026-27": "primary",               # Budget Paper 2
    "Federal Financial Relations_2026-27": "primary",   # Budget Paper 3
    "Agency Resourcing_2026_27_consolidated": "primary",# Official appropriations detail
    "womens-budget-statement-2026-27": "primary",       # Full official statement

    "budget-overview-2026-27": "summary",               # Plain-language overview
    "factsheet-backing-small-business": "summary",      # Simplified, audience-facing
    "factsheet-productivity": "summary",                # Simplified, audience-facing
    "tax-explainers-minimum-tax-discretionary-trusts": "summary",
    "tax-explainers-negative-gearing-capital-gains-tax": "summary",
    "tax-explainers-new-tax-cuts-workers": "summary",
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