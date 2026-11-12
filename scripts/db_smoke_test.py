# valuation-engine/scripts/db_smoke_test.py
from __future__ import annotations

import datetime as dt

from valuation_engine.infra.db.session import get_session
from valuation_engine.infra.db.repositories.stock_price_repo import (
    StockPriceRepository,
    StockPriceQuery,
)
from valuation_engine.infra.db.repositories.treasury_ytm_repo import TreasuryYTMRepository


def main() -> None:
    session_factory = get_session

    stock_repo = StockPriceRepository(session_factory)
    q = StockPriceQuery(
        stock_codes=["005930"],
        date_from=dt.date(2023, 1, 1),
        date_to=dt.date(2023, 12, 31),
        order="desc",
    )

    df_stock = stock_repo.fetch_adj_close_prices(q)
    print(df_stock.head())
    print(f"rows={len(df_stock)}\n")

    treasury_repo = TreasuryYTMRepository(session_factory)
    df_treasury = treasury_repo.fetch_treasury_ytm_range(
        date_from=dt.date(2023, 1, 1),
        date_to=dt.date(2023, 1, 31),
        order="desc",
    )
    print(df_treasury.head())
    print(f"rows={len(df_treasury)}")


if __name__ == "__main__":
    main()
