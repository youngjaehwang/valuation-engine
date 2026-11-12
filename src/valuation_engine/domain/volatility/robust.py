from __future__ import annotations

import numpy as np
import pandas as pd


def filter_returns_msd(returns: pd.Series, whisker_width: float = 2.5) -> pd.Series:
    """
    Legacy MSD filter.

    Parameters
    ----------
    returns : pd.Series
        Return series.
    whisker_width : float
        Scale factor.

    Returns
    -------
    pd.Series
        Filtered series.
    """
    r = returns.astype(float).dropna()
    std = float(np.std(r))
    mean = float(np.mean(r))
    upper = whisker_width * std + mean
    lower = -1.0 * (whisker_width * std - mean)
    return r[(r >= lower) & (r <= upper)]


def filter_returns_iqr(returns: pd.Series, whisker_width: float = 1.5) -> pd.Series:
    """
    IQR filter.

    Parameters
    ----------
    returns : pd.Series
        Return series.
    whisker_width : float
        Scale factor.

    Returns
    -------
    pd.Series
        Filtered series.
    """
    r = returns.astype(float).dropna()
    q1 = float(r.quantile(0.25))
    q3 = float(r.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - whisker_width * iqr
    upper = q3 + whisker_width * iqr
    return r[(r > lower) & (r < upper)]


def filter_returns_mad(returns: pd.Series, whisker_width: float = 2.5) -> pd.Series:
    """
    MAD filter (legacy coefficient 1.4826).

    Parameters
    ----------
    returns : pd.Series
        Return series.
    whisker_width : float
        Scale factor.

    Returns
    -------
    pd.Series
        Filtered series.
    """
    r = returns.astype(float).dropna().to_numpy()
    med = float(np.median(r))
    mad = 1.4826 * float(np.median(np.abs(r - med)))
    lower = med - whisker_width * mad
    upper = med + whisker_width * mad
    filtered = r[(r >= lower) & (r <= upper)]
    return pd.Series(filtered)


def apply_robust_filter(returns: pd.Series, method: str) -> pd.Series:
    """
    Apply robust filter by method name.

    Parameters
    ----------
    returns : pd.Series
        Return series.
    method : str
        'msd', 'mad', 'iqr', or 'none'.

    Returns
    -------
    pd.Series
        Filtered returns.
    """
    m = (method or "none").lower()
    if m == "msd":
        return filter_returns_msd(returns)
    if m == "mad":
        return filter_returns_mad(returns)
    if m == "iqr":
        return filter_returns_iqr(returns)
    return returns.astype(float).dropna()
