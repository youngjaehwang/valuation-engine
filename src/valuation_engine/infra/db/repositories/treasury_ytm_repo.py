# valuation_engine/infra/db/repositories/treasury_ytm_repo.py
from __future__ import annotations

import datetime as dt
import pandas as pd
from sqlalchemy import select

from valuation_engine.infra.db.models.market import TreasuryBondYTM
from valuation_engine.infra.db.session import SessionFactory


class TreasuryYTMRepository:
    """
    Treasury YTM repository for volatility and curve construction.
    """

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def fetch_treasury_ytm_range(
        self,
        *,
        date_from: dt.date,
        date_to: dt.date,
        order: str = "desc",
        drop_long_end: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch treasury YTM history.

        Parameters
        ----------
        date_from, date_to : date
            Inclusive date range.
        order : str
            'asc' or 'desc'.
        drop_long_end : bool
            If True, drop y20/y30/y50 to match legacy logic.

        Returns
        -------
        pd.DataFrame
            Treasury curve history by date.
        """
        if date_from > date_to:
            raise ValueError("date_from must be <= date_to")

        order_by = TreasuryBondYTM.credit_rating_date.asc() if order == "asc" else TreasuryBondYTM.credit_rating_date.desc()

        stmt = (
            select(TreasuryBondYTM)
            .where(TreasuryBondYTM.credit_rating_date >= date_from)
            .where(TreasuryBondYTM.credit_rating_date <= date_to)
            .order_by(order_by)
        )

        with self._session_factory() as session:
            rows = session.execute(stmt).scalars().all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([r.__dict__ for r in rows])
        df = df.drop(columns=["_sa_instance_state"], errors="ignore")

        if drop_long_end:
            df = df.drop(columns=["y20", "y30", "y50"], errors="ignore")

        return df.reset_index(drop=True)
