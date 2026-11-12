from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RFRVolatility:
    rfr_today: float
    daily_std: float
    annual_std: float


TENORS = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 15.0], dtype=float)


def yearfrac_30e360(d1, d2) -> float:
    """
    30E/360 year fraction (European 30/360).
    """
    a = d1.date() if hasattr(d1, "date") else d1
    b = d2.date() if hasattr(d2, "date") else d2
    d1_day = min(a.day, 30)
    d2_day = min(b.day, 30)
    return ((b.year - a.year) * 360 + (b.month - a.month) * 30 + (d2_day - d1_day)) / 360.0


def compute_rfr_volatility(
    treasury_df: pd.DataFrame,
    *,
    base_date,
    maturity_date,
    business_days: int,
    window: int,
    date_col: str = "credit_rating_date",
) -> RFRVolatility:
    """
    Compute RFR volatility from treasury yield history using legacy logic.

    Parameters
    ----------
    treasury_df : pd.DataFrame
        Rows are dates (DESC). Must contain tenor columns corresponding to TENORS.
    base_date, maturity_date
        Valuation date and instrument maturity.
    business_days : int
        Annualization factor.
    window : int
        Volatility period length (legacy: volatility_period).
    date_col : str
        Date column name.

    Returns
    -------
    RFRVolatility
        Today rfr level, daily std, annual std.
    """
    x = float(yearfrac_30e360(base_date, maturity_date))

    df = treasury_df.reset_index(drop=True).copy()

    col_map = {}
    for t in TENORS:
        if t in df.columns:
            col_map[t] = t
        elif str(t) in df.columns:
            col_map[t] = str(t)
        elif t.is_integer() and str(int(t)) in df.columns:
            col_map[t] = str(int(t))
        else:
            raise KeyError(f"Missing tenor column for tenor={t}")

    rate_mat = df[[col_map[t] for t in TENORS]].astype(float).to_numpy()
    remaining_t = np.interp(x, TENORS, rate_mat)  # vectorized across rows

    df["Remaining_T"] = remaining_t
    df = df.head(int(window) + 1).copy()

    r = np.log(df["Remaining_T"].astype(float) / df["Remaining_T"].astype(float).shift(-1))
    r = r.replace([np.inf, -np.inf], np.nan).dropna()

    daily_std = float(np.std(r.to_numpy()))
    annual_std = daily_std * math.sqrt(float(business_days))
    return RFRVolatility(rfr_today=float(df["Remaining_T"].iloc[0]), daily_std=daily_std, annual_std=annual_std)
