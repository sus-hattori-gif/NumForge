"""Country definitions and phone-number rules for NumForge.

The architecture is data-driven: to add a new country, append a new
`Country` entry. Rules are intentionally lightweight — length and
prefix checks only — so generation stays fast.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class CountryRules:
    """Lightweight local validation rules for a country.

    These rules are applied ONLY when the user enables --validate.
    They do NOT verify whether a number actually exists; they only
    reject combinations that are structurally impossible.
    """

    # Allowed total digit-lengths (after stripping formatting chars).
    allowed_lengths: Tuple[int, ...] = ()

    # Prefixes considered valid (mobile + landline). Empty = no check.
    valid_prefixes: Tuple[str, ...] = ()

    def is_valid(self, number: str) -> bool:
        """Return True if `number` passes length + prefix checks."""
        digits = re.sub(r"\D", "", number)

        # Strip leading +country-code or country-code prefix variants
        # so length check is performed on national-format numbers.
        if self.allowed_lengths and len(digits) not in self.allowed_lengths:
            return False

        if self.valid_prefixes:
            return any(digits.startswith(p) for p in self.valid_prefixes)

        return True


@dataclass(frozen=True)
class Country:
    """A country and its supported phone-number patterns."""

    id: str  # short slug used in CLI (e.g. "ir", "az")
    name: str
    code: str  # international dialing code, e.g. "+98"
    patterns: List[str] = field(default_factory=list)
    rules: CountryRules = field(default_factory=CountryRules)


# --- Iran ---------------------------------------------------------------
_IR_MOBILE = (
    "0901", "0902", "0903", "0905",
    "0910", "0911", "0912", "0913", "0914", "0915", "0916", "0917", "0918", "0919",
    "0990", "0991", "0992", "0993", "0994",
)
_IR_LANDLINE = (
    "021", "026", "031", "034", "041", "044", "051", "054", "056",
    "058", "061", "066", "071", "074", "076", "077", "081", "083", "084", "086", "087",
)

# --- Azerbaijan ---------------------------------------------------------
_AZ_MOBILE = ("050", "051", "055", "070", "077", "099")

# --- Turkey -------------------------------------------------------------
_TR_MOBILE = ("0505", "0532", "0533", "0534", "0535", "0536", "0537", "0538", "0539",
              "0541", "0542", "0543", "0544", "0545", "0546", "0547", "0548", "0549",
              "0551", "0552", "0553", "0554", "0555")

# --- United Kingdom -----------------------------------------------------
_UK_MOBILE = ("074", "075", "076", "077", "078", "079")


COUNTRIES: List[Country] = [
    Country(
        id="ir",
        name="Iran",
        code="+98",
        patterns=[
            "09XXXXXXXXX",
            "98XXXXXXXXXX",
            "+98XXXXXXXXXX",
            "0912XXX1234",
            "0912XXXXXXX",
        ],
        rules=CountryRules(
            allowed_lengths=(10, 11, 12),
            valid_prefixes=_IR_MOBILE + _IR_LANDLINE,
        ),
    ),
    Country(
        id="az",
        name="Azerbaijan",
        code="+994",
        patterns=[
            "0XXXXXXXXX",
            "994XXXXXXXXX",
            "+994XXXXXXXXX",
            "050XXXXXXX",
            "055XXXXXXX",
        ],
        rules=CountryRules(
            allowed_lengths=(9, 10, 12),
            valid_prefixes=_AZ_MOBILE,
        ),
    ),
    Country(
        id="tr",
        name="Turkey",
        code="+90",
        patterns=[
            "0XXXXXXXXXX",
            "90XXXXXXXXXX",
            "+90XXXXXXXXXX",
            "05XXXXXXXX",
        ],
        rules=CountryRules(
            allowed_lengths=(10, 11, 12),
            valid_prefixes=_TR_MOBILE,
        ),
    ),
    Country(
        id="us",
        name="United States",
        code="+1",
        patterns=[
            "1XXXXXXXXXX",
            "+1XXXXXXXXXX",
            "XXXXXXXXXX",
            "XXX-XXX-XXXX",
            "(XXX) XXX-XXXX",
        ],
        rules=CountryRules(
            allowed_lengths=(10, 11),
            valid_prefixes=(),  # NANP rules too complex for a light check
        ),
    ),
    Country(
        id="uk",
        name="United Kingdom",
        code="+44",
        patterns=[
            "0XXXXXXXXXX",
            "44XXXXXXXXXX",
            "+44XXXXXXXXXX",
            "07XXXXXXXXX",
        ],
        rules=CountryRules(
            allowed_lengths=(10, 11, 12),
            valid_prefixes=_UK_MOBILE,
        ),
    ),
]


# --- Lookup helpers -----------------------------------------------------

def get_country_by_index(index: int) -> Country:
    """Return the Country at a given 1-based index."""
    if not 1 <= index <= len(COUNTRIES):
        raise IndexError(f"Country index out of range: {index}")
    return COUNTRIES[index - 1]


def get_country_by_id(country_id: str) -> Country:
    """Return the Country with the given short id (case-insensitive)."""
    cid = country_id.strip().lower()
    for c in COUNTRIES:
        if c.id == cid:
            return c
    raise KeyError(f"Unknown country id: '{country_id}'")


def list_country_ids() -> tuple[str, ...]:
    """Return all country ids."""
    return tuple(c.id for c in COUNTRIES)