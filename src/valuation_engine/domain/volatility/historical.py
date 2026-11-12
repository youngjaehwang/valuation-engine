from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .returns import log_returns_descending
from .robust import apply_robust_filter


@dataclass(frozen=True)
class EquityVolatility:
    daily_filtered: float
    daily_raw: float
    annual_filtered: float
    annual_raw: float


def compute_equity_volatility(
    prices_df: pd.DataFrame,
    *,
    business_days: int,
    window: int,
    robust_method: str = "msd",
    date_col: str = "price_date",
    price_col: str = "adj_close_price",
) -> tuple[EquityVolatility, pd.DataFrame, pd.DataFrame]:
    """
    Compute equity volatility using legacy logic.

    Parameters
    ----------
    prices_df : pd.DataFrame
        Must contain date_col and price_col, ordered DESC by date.
    business_days : int
        Annualization factor (legacy: count_business_day).
    window : int
        Volatility period (legacy: term).
    robust_method : str
        'msd', 'mad', 'iqr', 'none'.
    date_col : str
        Date column name.
    price_col : str
        Price column name.

    Returns
    -------
    (EquityVolatility, raw_detail, filtered_detail)
        raw_detail and filtered_detail are report/export friendly frames.
    """
    df = prices_df[[date_col, price_col]].copy()
    df = df.dropna()
    df[price_col] = df[price_col].astype(float)

    df["returns"] = log_returns_descending(df[price_col])
    df = df.dropna().head(int(window) + 1).copy()

    raw_returns = df["returns"]
    filtered_returns = apply_robust_filter(raw_returns, robust_method)

    daily_raw = float(np.std(raw_returns.astype(float)))
    daily_filtered = float(np.std(filtered_returns.astype(float)))

    annual_raw = daily_raw * math.sqrt(float(business_days))
    annual_filtered = daily_filtered * math.sqrt(float(business_days))

    result = EquityVolatility(
        daily_filtered=daily_filtered,
        daily_raw=daily_raw,
        annual_filtered=annual_filtered,
        annual_raw=annual_raw,
    )

    raw_detail = df.rename(columns={date_col: "date", price_col: "price"}).copy()
    filtered_detail = raw_detail[raw_detail["returns"].isin(filtered_returns)].copy()

    return result, raw_detail, filtered_detail
