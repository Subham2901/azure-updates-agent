"""Load, validate, and verify the service watchlist.

The watchlist is the scope boundary of the whole tool (requirement #2).
Names must match Microsoft's taxonomy exactly — 'eq' filters are exact —
so we verify every entry against live server facets before any run.
Rationale: an unvalidated name silently matches zero records forever
(observed: 'Azure Kubernetes Service' vs 'Azure Kubernetes Service (AKS)',
612 records missed, 2026-07-10).
"""

from __future__ import annotations

import difflib
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Watchlist(BaseModel):
    """Validated watchlist configuration."""

    model_config = ConfigDict(frozen=True)

    products: tuple[str, ...] = Field(min_length=1)
    tags: tuple[str, ...] = ()


class WatchlistValidationError(Exception):
    """Raised when watchlist entries don't match the live taxonomy."""


def load_watchlist(path: Path) -> Watchlist:
    """Parse and structurally validate the YAML watchlist."""
    raw = yaml.safe_load(path.read_text())
    return Watchlist.model_validate(raw)


def verify_against_taxonomy(
    watchlist: Watchlist, known_products: set[str]
) -> None:
    """Fail loudly, with suggestions, if any watched name is unknown.

    A name absent from the taxonomy would silently match nothing —
    the exact failure this tool exists to prevent.
    """
    problems: list[str] = []
    for name in watchlist.products:
        if name not in known_products:
            suggestions = difflib.get_close_matches(
                name, known_products, n=3, cutoff=0.5
            )
            hint = f" Did you mean: {suggestions}?" if suggestions else ""
            problems.append(f"Unknown product {name!r}.{hint}")
    if problems:
        raise WatchlistValidationError("\n".join(problems))