from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pandas as pd

from valuation_engine.domain.spotrate.builder import build_spotrate_corp_and_rf
from valuation_engine.infra.marketdata.corp_repository import fetch_corp_ytm_curve
from valuation_engine.infra.marketdata.treasury_repository import fetch_treasury_ytm_curve


@dataclass(frozen=True)
class SpotrateRequest:
    """Spotrate request.

    Parameters
    ----------
    base_date:
        Valuation base date.
    maturity_date:
        Bond maturity date. (Kept for interface compatibility; not required by curve build itself.)
    credit_rating:
        Credit rating value used in CreditRating.credit_rating_value (e.g., 'AA+', 'A0').
    data_source:
        'KIS' or others (mapped to KIS vs FNP tables).
    corp_bond_type_code:
        Corporate bond_type_code in bond_ytm table.
    ytm_limit_years:
        Curve horizon (years). Must match original logic (default 15).
    """
    base_date: dt.date
    maturity_date: dt.date
    credit_rating: str
    data_source: str = "KIS"
    corp_bond_type_code: str = "CB"
    ytm_limit_years: int = 15


@dataclass(frozen=True)
class SpotrateResponse:
    """Spotrate response."""
    used_corp_date: dt.date
    used_treasury_date: dt.date
    curve: pd.DataFrame


class SpotrateService:
    """Application service for spotrate curve building."""

    def build_spotrate(self, req: SpotrateRequest) -> SpotrateResponse:
        """Build spotrate curve (corp + treasury) end-to-end.

        Returns
        -------
        SpotrateResponse
            curve columns include:
            ['TTM','thirty360_yearfrac','actual365_yearfrac','YTM','DF','ZCR','YTM_rf','DF_rf','ZCR_rf']
        """
        used_corp_date, corp_ytm = fetch_corp_ytm_curve(
            req.base_date,
            credit_rating_value=req.credit_rating,
            bond_type_code=req.corp_bond_type_code,
            data_source=req.data_source,
        )

        used_rf_date, rf_ytm = fetch_treasury_ytm_curve(
            req.base_date,
            filter_to_half_year=True,
        )

        curve = build_spotrate_corp_and_rf(
            base_date=req.base_date,
            corp_ytm_df=corp_ytm,
            treasury_ytm_df=rf_ytm,
            ytm_limit_years=req.ytm_limit_years,
        )

        return SpotrateResponse(
            used_corp_date=used_corp_date,
            used_treasury_date=used_rf_date,
            curve=curve,
        )
