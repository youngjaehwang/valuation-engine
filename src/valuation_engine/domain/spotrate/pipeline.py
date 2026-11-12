from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd
import QuantLib as ql
from scipy.interpolate import interp1d


@dataclass(frozen=True)
class CurveGrid:
    """Curve grid outputs."""
    ttm: np.ndarray
    thirty360_yearfrac: np.ndarray
    actual365_yearfrac: np.ndarray


class SpotrateCurvePipeline:
    """Par-YTM based spotrate builder (DF bootstrap + ZCR).

    This class intentionally mirrors the original implementation logic
    to preserve behavior, then we can fix/upgrade step-by-step later.
    """

    def __init__(
        self,
        base_date: dt.date,
        ytm_limit_years: int = 15,
        coupon_months: int = 3,
    ):
        self._ytm_limit_years = int(ytm_limit_years)
        self._coupon_months = int(coupon_months)

        self._calendar = ql.SouthKorea()
        self._dc_act365 = ql.Actual365Fixed()
        self._dc_30_360 = ql.Thirty360(ql.Thirty360.BondBasis)

        self._base = ql.Date(base_date.day, base_date.month, base_date.year)
        self._effective = self._advance_to_business_day(self._base + 1)
        self._termination = self._calendar.advance(
            self._effective, ql.Period(self._ytm_limit_years, ql.Years)
        )

        self._schedule = self._build_schedule(
            self._effective,
            self._termination,
            self._coupon_months,
        )

    def build_from_par_ytm(self, ytm_df: pd.DataFrame) -> pd.DataFrame:
        """Build interpolated YTM, DF, and ZCR on the coupon grid.

        Parameters
        ----------
        ytm_df:
            DataFrame with columns ['TTM', 'YTM'].
            YTM is expected as percent (e.g., 3.25 for 3.25%).

        Returns
        -------
        pandas.DataFrame
            Columns: ['TTM', 'thirty360_yearfrac', 'actual365_yearfrac', 'YTM', 'DF', 'ZCR']
        """
        ytm_df = self._validate_ytm_input(ytm_df)

        grid = self._make_grid()
        interp = self._interpolate_par_ytm(ytm_df, grid)
        df = self._bootstrap_discount_factor(interp)
        out = self._compute_zcr(df, grid)

        out = out[
            ["TTM", "thirty360_yearfrac", "actual365_yearfrac", "YTM", "DF", "ZCR"]
        ].copy()
        return out

    def _advance_to_business_day(self, d: ql.Date) -> ql.Date:
        if self._calendar.isBusinessDay(d):
            return d
        return self._calendar.advance(d, 1, ql.Days)

    def _build_schedule(
        self,
        effective: ql.Date,
        termination: ql.Date,
        coupon_months: int,
    ) -> ql.Schedule:
        return ql.Schedule(
            effective,
            termination,
            ql.Period(coupon_months, ql.Months),
            self._calendar,
            ql.Following,
            ql.Following,
            ql.DateGeneration.Forward,
            False,
        )

    def _make_grid(self) -> CurveGrid:
        coupon_year = self._coupon_months / 12.0

        # TTM in years on coupon grid: (coupon_year, 2*coupon_year, ..., ytm_limit_years)
        ttm = np.arange(
            coupon_year,
            self._ytm_limit_years + coupon_year,
            coupon_year,
            dtype=float,
        )

        # schedule index 0 is effective_date; we use schedule[1:] as cashflow dates
        n = len(self._schedule) - 1
        if n != len(ttm):
            # Keep original behavior strictness: schedule should align with TTM grid
            # If mismatch occurs (calendar/roll), we still use schedule dates as truth
            ttm = np.arange(coupon_year, coupon_year * (n + 1), coupon_year, dtype=float)

        thirty360 = np.array(
            [self._dc_30_360.yearFraction(self._base, self._schedule[i]) for i in range(1, len(self._schedule))],
            dtype=float,
        )
        act365 = np.array(
            [self._dc_act365.yearFraction(self._base, self._schedule[i]) for i in range(1, len(self._schedule))],
            dtype=float,
        )
        return CurveGrid(ttm=ttm, thirty360_yearfrac=thirty360, actual365_yearfrac=act365)

    def _validate_ytm_input(self, ytm_df: pd.DataFrame) -> pd.DataFrame:
        if not {"TTM", "YTM"}.issubset(ytm_df.columns):
            raise ValueError("ytm_df must contain columns ['TTM', 'YTM'].")

        out = ytm_df[["TTM", "YTM"]].copy()
        out["TTM"] = out["TTM"].astype(float)
        out["YTM"] = out["YTM"].astype(float)
        out = out.dropna().sort_values("TTM").reset_index(drop=True)
        if out.empty:
            raise ValueError("ytm_df has no valid rows after cleaning.")
        return out

    def _interpolate_par_ytm(self, ytm_df: pd.DataFrame, grid: CurveGrid) -> pd.DataFrame:
        """Linear interpolation onto every coupon date (original mapping preserved)."""
        coupon_months = self._coupon_months
        factor = 12 / coupon_months  # 3M -> 4, 6M -> 2

        # Map input TTMs to schedule indices as in original code:
        # schedule[int(TTM * factor)]
        x = []
        y = []
        for ttm, ytm_pct in zip(ytm_df["TTM"].to_numpy(), ytm_df["YTM"].to_numpy()):
            idx = int(ttm * factor)
            if idx <= 0 or idx >= len(self._schedule):
                # Out of range points are ignored (original behavior effectively assumes within limit)
                continue
            x.append(self._dc_30_360.yearFraction(self._base, self._schedule[idx]))
            y.append(ytm_pct * 0.01)

        if len(x) < 2:
            raise ValueError("Not enough YTM points to interpolate on the coupon grid.")

        func = interp1d(np.array(x, dtype=float), np.array(y, dtype=float), kind="linear", fill_value="extrapolate")
        y_new = func(grid.thirty360_yearfrac)

        return pd.DataFrame(
            {
                "TTM": grid.ttm,
                "thirty360_yearfrac": grid.thirty360_yearfrac,
                "YTM": y_new,
            }
        )

    def _bootstrap_discount_factor(self, interp_df: pd.DataFrame) -> pd.DataFrame:
        """Bootstrap DF using coupon PV condition (original formula preserved)."""
        df = interp_df.copy()

        delta_t = np.diff(df["thirty360_yearfrac"].to_numpy(), prepend=np.nan)
        base_to_effective = self._dc_30_360.yearFraction(self._base, self._effective)
        delta_t[0] = df["thirty360_yearfrac"].iloc[0] - base_to_effective

        y = df["YTM"].to_numpy(dtype=float)
        df_out = np.empty(len(df), dtype=float)

        df0 = 1.0
        df_out[0] = (1.0 / (1.0 + y[0] * delta_t[0])) * df0

        for i in range(1, len(df)):
            acc = np.sum(df_out[:i] * delta_t[:i])
            df_out[i] = (df0 - y[i] * acc) / (1.0 + y[i] * delta_t[i])

        df["DF"] = df_out
        return df

    def _compute_zcr(self, df: pd.DataFrame, grid: CurveGrid) -> pd.DataFrame:
        """Compute continuous-compounded zero coupon rate (original convention preserved)."""
        out = df.copy()
        out["actual365_yearfrac"] = grid.actual365_yearfrac

        base_to_effective = self._dc_act365.yearFraction(self._base, self._effective)
        denom = out["actual365_yearfrac"].to_numpy(dtype=float) - base_to_effective

        if np.any(denom <= 0.0):
            raise ValueError("Invalid year fraction grid (denominator <= 0).")

        out["ZCR"] = -np.log(out["DF"].to_numpy(dtype=float)) / denom
        return out
