from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pandas as pd

from valuation_engine.domain.spotrate.pipeline import SpotrateCurvePipeline


@dataclass(frozen=True)
class SpotrateBuildParams:
    """Spotrate build parameters.

    Parameters
    ----------
    ytm_limit_years:
        Maximum horizon in years for the curve build.
    corp_coupon_months:
        Coupon interval (months) for corporate par curve bootstrap.
    rf_coupon_months:
        Coupon interval (months) for treasury par curve bootstrap.
    """
    ytm_limit_years: int = 15
    corp_coupon_months: int = 3
    rf_coupon_months: int = 6


def build_spotrate_corp_and_rf(
    base_date: dt.date,
    corp_ytm_df: pd.DataFrame,
    treasury_ytm_df: pd.DataFrame,
    ytm_limit_years: int = 15,
) -> pd.DataFrame:
    """Build corporate and treasury spotrate curves and merge them.

    Notes
    -----
    - This follows the original logic:
      1) effective_date = base_date + 1 business day (KR calendar, Following)
      2) schedule built from effective_date to effective_date + ytm_limit_years
      3) linear interpolation of YTM onto every coupon grid date
      4) bootstrap discount factors using coupon PV condition
      5) compute continuous-compounded zero rate (ZCR) from DF
      6) merge corp and rf curves on TTM grid
    """
    params = SpotrateBuildParams(ytm_limit_years=ytm_limit_years)

    corp_pipe = SpotrateCurvePipeline(
        base_date=base_date,
        ytm_limit_years=params.ytm_limit_years,
        coupon_months=params.corp_coupon_months,
    )
    corp_curve = corp_pipe.build_from_par_ytm(corp_ytm_df)

    rf_pipe = SpotrateCurvePipeline(
        base_date=base_date,
        ytm_limit_years=params.ytm_limit_years,
        coupon_months=params.rf_coupon_months,
    )
    rf_curve = rf_pipe.build_from_par_ytm(treasury_ytm_df)

    rf_curve = rf_curve.rename(
        columns={"YTM": "YTM_rf", "DF": "DF_rf", "ZCR": "ZCR_rf"}
    )

    out = pd.merge(
        corp_curve,
        rf_curve[["TTM", "YTM_rf", "DF_rf", "ZCR_rf"]],
        on="TTM",
        how="left",
    )
    return out
