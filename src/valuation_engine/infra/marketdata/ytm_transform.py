from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from valuation_engine.infra.marketdata.tenor_map import TenorSpec


def wide_row_to_long_ytm(
    wide_df: pd.DataFrame,
    tenors: Iterable[TenorSpec],
    *,
    keep_null: bool = False,
    require_min_points: int = 2,
) -> pd.DataFrame:
    """Transform a wide par-YTM row into a long curve.

    Parameters
    ----------
    wide_df:
        DataFrame with exactly one row containing tenor columns (e.g., m3, y1, y10, ...).
    tenors:
        Tenor specs mapping column names to TTM in years.
    keep_null:
        If True, keep NaN YTM rows; otherwise drop them.
    require_min_points:
        Minimum number of non-null points required for curve building.

    Returns
    -------
    pandas.DataFrame
        Columns: ['TTM', 'YTM'] where YTM is in annual percent as stored in DB.

    Raises
    ------
    ValueError
        If input has not exactly one row, or not enough points exist.
    """
    if wide_df is None or wide_df.empty:
        raise ValueError("wide_df is empty.")
    if len(wide_df) != 1:
        raise ValueError("wide_df must contain exactly one row.")

    row = wide_df.iloc[0]
    ttm = []
    ytm = []

    for spec in tenors:
        if spec.column not in wide_df.columns:
            continue
        val = row[spec.column]
        if pd.isna(val) and not keep_null:
            continue
        ttm.append(float(spec.ttm_years))
        ytm.append(np.nan if pd.isna(val) else float(val))

    out = pd.DataFrame({"TTM": ttm, "YTM": ytm}).sort_values("TTM").reset_index(drop=True)

    if not keep_null:
        non_null = out["YTM"].notna().sum()
        if non_null < require_min_points:
            raise ValueError(f"Not enough YTM points: {non_null} < {require_min_points}")

    return out


def filter_half_year_grid(ytm_df: pd.DataFrame) -> pd.DataFrame:
    """Keep only half-year multiples (TTM % 0.5 == 0)."""
    df = ytm_df.copy()
    df["TTM"] = df["TTM"].astype(float)
    return df[(df["TTM"] % 0.5) == 0.0].reset_index(drop=True)
