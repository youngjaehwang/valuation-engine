from __future__ import annotations

import numpy as np
import pandas as pd


def log_returns_descending(
    series: pd.Series,
) -> pd.Series:
    """
    Compute log returns for a series ordered in descending time.

    Notes
    -----
    This preserves the legacy definition:
    r_t = log(x_t / x_{t+1})

    Parameters
    ----------
    series : pd.Series
        Positive level series (e.g., price, yield), ordered by date DESC.

    Returns
    -------
    pd.Series
        Log return series (NaNs removed).
    """
    x = series.astype(float)
    r = np.log(x / x.shift(-1))
    return r.replace([np.inf, -np.inf], np.nan).dropna()
