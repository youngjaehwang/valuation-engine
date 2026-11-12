from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from valuation_engine.infra.db.models.market import Company


class CompanyRepository:
    """Company repository."""

    def exists(self, session: Session, stock_code: str) -> bool:
        stmt = select(Company.stock_code).where(Company.stock_code == stock_code).limit(1)
        return session.execute(stmt).first() is not None

    def search_by_name(
        self,
        session: Session,
        *,
        corp_name: str,
        exact: bool = False,
        order: str = "asc",
        limit: int | None = 50,
    ) -> list[dict]:
        query = select(Company.stock_code, Company.corp_name, Company.market)
        if corp_name:
            if exact:
                query = query.where(Company.corp_name == corp_name)
            else:
                query = query.where(Company.corp_name.like(f"{corp_name}%"))

        query = query.order_by(text(f"corp_name {order}"))
        if limit is not None:
            query = query.limit(int(limit))

        rows = session.execute(query).all()
        return [{"stockcode": r[0], "stockname": r[1], "market": r[2].name} for r in rows]
