from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from valuation_engine.infra.db.models.market import CreditRating


class CreditRatingRepository:
    """Credit rating repository."""

    def exists_credit_rating_value(self, session: Session, credit_rating_value: str) -> bool:
        """Return True if credit_rating_value exists."""
        stmt = (
            select(CreditRating.credit_rating_value)
            .where(CreditRating.credit_rating_value == credit_rating_value)
            .limit(1)
        )
        return session.execute(stmt).first() is not None

    def list_by_bond_type(self, session: Session, bond_type_code: str) -> list[tuple[str, str]]:
        """Return list of (credit_rating_value, credit_rating_name) for a bond type."""
        stmt = (
            select(CreditRating.credit_rating_value, CreditRating.credit_rating_name)
            .where(CreditRating.bond_type_code == bond_type_code)
            .order_by(CreditRating.credit_rating_value.asc())
        )
        return [(r[0], r[1]) for r in session.execute(stmt).all()]