"""Country definitions and phone-number patterns for NumForge.

The architecture is data-driven: to add a new country, simply append a
new entry to the COUNTRIES list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Country:
    """A country and its supported phone-number patterns."""

    name: str
    code: str  # international dialing code, e.g. "+98"
    patterns: List[str] = field(default_factory=list)


# Each pattern uses "X" as the placeholder for an unknown digit.
COUNTRIES: List[Country] = [
    Country(
        name="Iran",
        code="+98",
        patterns=[
            "09XXXXXXXXX",
            "98XXXXXXXXXX",
            "+98XXXXXXXXXX",
            "0912XXX1234",
            "0912XXXXXXX",
        ],
    ),
    Country(
        name="Azerbaijan",
        code="+994",
        patterns=[
            "0XXXXXXXXX",
            "994XXXXXXXXX",
            "+994XXXXXXXXX",
            "050XXXXXXX",
            "055XXXXXXX",
        ],
    ),
    Country(
        name="Turkey",
        code="+90",
        patterns=[
            "0XXXXXXXXXX",
            "90XXXXXXXXXX",
            "+90XXXXXXXXXX",
            "05XXXXXXXX",
        ],
    ),
    Country(
        name="United States",
        code="+1",
        patterns=[
            "1XXXXXXXXXX",
            "+1XXXXXXXXXX",
            "XXXXXXXXXX",
            "XXX-XXX-XXXX",
            "(XXX) XXX-XXXX",
        ],
    ),
    Country(
        name="United Kingdom",
        code="+44",
        patterns=[
            "0XXXXXXXXXX",
            "44XXXXXXXXXX",
            "+44XXXXXXXXXX",
            "07XXXXXXXXX",
        ],
    ),
]


def get_country_by_index(index: int) -> Country:
    """Return the Country at a given 1-based index."""
    if not 1 <= index <= len(COUNTRIES):
        raise IndexError(f"Country index out of range: {index}")
    return COUNTRIES[index - 1]