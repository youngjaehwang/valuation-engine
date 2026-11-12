from __future__ import annotations

import datetime as dt
import pandas as pd

from valuation_engine.infra.db.session import session_scope
from valuation_engine.infra.db.repositories.bond_ytm_repo import BondYTMRepository
from valuation_engine.infra.marketdata.tenor_map import CORP_TENORS
from valuation_engine.infra.marketdata.ytm_transform import wide_row_to_long_ytm


def fetch_corp_ytm_curve(
    base_date: dt.date,
    *,
    credit_rating_value: str,
    bond_type_code: str = "CB",
    data_source: str = "KIS",
    fallback_days: int = 3650,
) -> tuple[dt.date, pd.DataFrame]:
    """Fetch corporate par-YTM curve as long DataFrame.

    Returns
    -------
    (used_date, ytm_df)
        ytm_df columns: ['TTM','YTM'] (annual percent)
    """
    repo = BondYTMRepository()

    with session_scope() as session:
        used_date, orm_row = repo.get_valid_wide_row(
            session=session,
            data_source=data_source,
            bond_type_code=bond_type_code,
            target_date=base_date,
            credit_rating_value=credit_rating_value,
            fallback_days=fallback_days,
        )

        # ORM row → DataFrame(1 row)
        wide_df = pd.DataFrame([orm_row.__dict__])
        wide_df = wide_df.drop(columns=["_sa_instance_state"], errors="ignore")

    ytm_df = wide_row_to_long_ytm(wide_df, CORP_TENORS)
    return used_date, ytm_df
