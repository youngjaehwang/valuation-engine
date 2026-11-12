from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TenorSpec:
    """Tenor mapping specification.

    Attributes
    ----------
    column:
        Column name in DB wide table (e.g., 'm3', 'y15a').
    ttm_years:
        Time-to-maturity in years (e.g., 0.25, 1.5).
    """
    column: str
    ttm_years: float


CORP_TENORS: tuple[TenorSpec, ...] = (
    TenorSpec("m3", 0.25),
    TenorSpec("m6", 0.50),
    TenorSpec("m9", 0.75),
    TenorSpec("y1", 1.00),
    TenorSpec("y15a", 1.50),
    TenorSpec("y2", 2.00),
    TenorSpec("y25", 2.50),
    TenorSpec("y3", 3.00),
    TenorSpec("y5", 5.00),
    TenorSpec("y7", 7.00),
    TenorSpec("y10", 10.00),
    TenorSpec("y15", 15.00),
    TenorSpec("y20", 20.00),
    TenorSpec("y30", 30.00),
    TenorSpec("y50", 50.00),
)

TREASURY_TENORS: tuple[TenorSpec, ...] = (
    TenorSpec("m3", 0.25),
    TenorSpec("m6", 0.50),
    TenorSpec("m9", 0.75),
    TenorSpec("y1", 1.00),
    TenorSpec("y15a", 1.50),
    TenorSpec("y2", 2.00),
    TenorSpec("y25", 2.50),
    TenorSpec("y3", 3.00),
    TenorSpec("y4", 4.00),
    TenorSpec("y5", 5.00),
    TenorSpec("y7", 7.00),
    TenorSpec("y10", 10.00),
    TenorSpec("y15", 15.00),
    TenorSpec("y20", 20.00),
    TenorSpec("y30", 30.00),
    TenorSpec("y50", 50.00),
)


def columns_of(tenors: Iterable[TenorSpec]) -> list[str]:
    """Return ordered column names from tenor specs."""
    return [t.column for t in tenors]
