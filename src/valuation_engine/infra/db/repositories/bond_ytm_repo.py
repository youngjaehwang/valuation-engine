from __future__ import annotations

import datetime as dt
from typing import Type

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from valuation_engine.infra.db.models.market import BondYTM, BondYTMFNP, CreditRating


class BondYTMRepository:
    """Corporate bond par-YTM repository (wide row)."""

    def _table(self, data_source: str) -> Type[BondYTM] | Type[BondYTMFNP]:
        """Select table by data_source."""
        if data_source.upper() == "KIS":
            return BondYTM
        return BondYTMFNP

    def get_wide_row(
        self,
        session: Session,
        *,
        data_source: str,
        bond_type_code: str,
        credit_rating_date: dt.date,
        credit_rating_value: str,
    ):
        """Get a single wide row for the given date and rating.

        Returns
        -------
        ORM row (BondYTM/BondYTMFNP) or None
        """
        table = self._table(data_source)

        stmt = (
            select(table)
            .join(
                CreditRating,
                and_(
                    table.bond_type_code == CreditRating.bond_type_code,
                    table.credit_rating_code == CreditRating.credit_rating_code,
                ),
            )
            .where(
                table.bond_type_code == bond_type_code,
                table.credit_rating_date == credit_rating_date,
                CreditRating.credit_rating_value == credit_rating_value,
            )
            .limit(1)
        )
        return session.execute(stmt).scalars().first()

    def get_valid_wide_row(
        self,
        session: Session,
        *,
        data_source: str,
        bond_type_code: str,
        target_date: dt.date,
        credit_rating_value: str,
        fallback_days: int = 3650,
    ) -> tuple[dt.date, object]:
        """Fallback to previous dates until a wide row is found.

        Returns
        -------
        (used_date, orm_row)
        """
        cur = target_date
        min_date = target_date - dt.timedelta(days=int(fallback_days))

        while cur >= min_date:
            row = self.get_wide_row(
                session,
                data_source=data_source,
                bond_type_code=bond_type_code,
                credit_rating_date=cur,
                credit_rating_value=credit_rating_value,
            )
            if row is not None:
                return cur, row
            cur = cur - dt.timedelta(days=1)

        raise ValueError(
            f"No corporate YTM data found: rating={credit_rating_value}, "
            f"bond_type={bond_type_code}, source={data_source}, "
            f"within fallback_days={fallback_days} from {target_date}."
        )
