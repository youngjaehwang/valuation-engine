from __future__ import annotations

import datetime as dt
import pandas as pd

from valuation_engine.infra.db.session import session_scope
from valuation_engine.infra.db.repositories.treasury_ytm_repo import TreasuryYTMRepository
from valuation_engine.infra.marketdata.tenor_map import TREASURY_TENORS
from valuation_engine.infra.marketdata.ytm_transform import (
    wide_row_to_long_ytm,
    filter_half_year_grid,
)


def fetch_treasury_ytm_curve(
    base_date: dt.date,
    *,
    filter_to_half_year: bool = True,
    fallback_days: int = 3650,
) -> tuple[dt.date, pd.DataFrame]:
    """Fetch treasury par-YTM curve as long DataFrame.

    Returns
    -------
    (used_date, ytm_df)
        ytm_df columns: ['TTM','YTM'] (annual percent)
    """
    repo = TreasuryYTMRepository()

    with session_scope() as session:
        used_date, orm_row = repo.get_valid_wide_row(
            session=session,
            target_date=base_date,
            fallback_days=fallback_days,
        )

        wide_df = pd.DataFrame([orm_row.__dict__])
        wide_df = wide_df.drop(columns=["_sa_instance_state"], errors="ignore")

    ytm_df = wide_row_to_long_ytm(wide_df, TREASURY_TENORS)

    if filter_to_half_year:
        ytm_df = filter_half_year_grid(ytm_df)

    return used_date, ytm_df
