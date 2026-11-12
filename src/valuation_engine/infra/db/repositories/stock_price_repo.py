# valuation_engine/infra/db/repositories/stock_price_repo.py
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, Literal

import pandas as pd
from sqlalchemy import Select, select

from valuation_engine.infra.db.models.market import Company, MarketType, StockPrice
from valuation_engine.infra.db.session import SessionFactory


Order = Literal["asc", "desc"]


@dataclass(frozen=True)
class StockPriceQuery:
    stock_codes: list[str]
    date_from: dt.date
    date_to: dt.date
    order: Order = "desc"


class StockPriceRepository:
    """
    Stock price repository optimized for small number of tickers (<=10)
    and long horizons (<=20y).
    """

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def fetch_adj_close_prices(
        self,
        q: StockPriceQuery,
    ) -> pd.DataFrame:
        """
        Fetch adjusted close prices for one or more tickers within a date range.

        Parameters
        ----------
        q : StockPriceQuery
            Query parameters.

        Returns
        -------
        pd.DataFrame
            Columns: ['price_date', 'stock_code', 'adj_close_price']
            Sorted by (stock_code, price_date) according to q.order.
        """
        if not q.stock_codes:
            raise ValueError("stock_codes must not be empty")
        if q.date_from > q.date_to:
            raise ValueError("date_from must be <= date_to")

        order_by = StockPrice.price_date.asc() if q.order == "asc" else StockPrice.price_date.desc()

        stmt: Select = (
            select(StockPrice.price_date, StockPrice.stock_code, StockPrice.adj_close_price)
            .where(StockPrice.stock_code.in_(q.stock_codes))
            .where(StockPrice.price_date >= q.date_from)
            .where(StockPrice.price_date <= q.date_to)
            .order_by(StockPrice.stock_code.asc(), order_by)
        )

        with self._session_factory() as session:
            rows = session.execute(stmt).all()

        df = pd.DataFrame(rows, columns=["price_date", "stock_code", "adj_close_price"])
        return df

    def fetch_adj_close_prices_with_market_fill(
        self,
        q: StockPriceQuery,
        *,
        fillna: bool,
    ) -> pd.DataFrame:
        """
        Fetch prices and optionally fill missing company prices with market index prices.

        Notes
        -----
        This replicates the legacy behavior:
        - If a ticker has missing prices, load its market index (KOSPI/KOSDAQ)
          and fill missing values by date.

        Parameters
        ----------
        q : StockPriceQuery
            Query parameters.
        fillna : bool
            If True, fill missing values using market index series.

        Returns
        -------
        pd.DataFrame
            Columns:
            - price_date
            - stock_code
            - adj_close_price
            - (optional) adj_close_price_market, stock_code_market (intermediate columns not returned)
        """
        base_df = self.fetch_adj_close_prices(q)

        if not fillna:
            return base_df

        if base_df.empty:
            return base_df

        out_frames: list[pd.DataFrame] = []
        for code in q.stock_codes:
            df_code = base_df[base_df["stock_code"] == code].copy()
            if df_code.empty:
                continue

            if df_code["adj_close_price"].isna().any():
                market_code = self._resolve_market_index_code(code)
                if market_code is not None:
                    q_market = StockPriceQuery(
                        stock_codes=[market_code],
                        date_from=q.date_from,
                        date_to=q.date_to,
                        order=q.order,
                    )
                    df_mkt = self.fetch_adj_close_prices(q_market)
                    merged = pd.merge(
                        df_code,
                        df_mkt.rename(
                            columns={
                                "stock_code": "stock_code_market",
                                "adj_close_price": "adj_close_price_market",
                            }
                        ),
                        on="price_date",
                        how="outer",
                    )
                    merged["adj_close_price"] = merged["adj_close_price"].fillna(merged["adj_close_price_market"])
                    merged["stock_code"] = merged["stock_code"].fillna(code)
                    merged = merged[["price_date", "stock_code", "adj_close_price"]]
                    out_frames.append(merged)
                    continue

            out_frames.append(df_code[["price_date", "stock_code", "adj_close_price"]])

        if not out_frames:
            return base_df[["price_date", "stock_code", "adj_close_price"]]

        result = pd.concat(out_frames, axis=0, ignore_index=True)
        order_by = ["stock_code", "price_date"]
        result = result.sort_values(order_by, ascending=[True, q.order == "asc"])
        return result.reset_index(drop=True)

    def _resolve_market_index_code(self, stock_code: str) -> str | None:
        """
        Resolve market index code for a given stock.

        Returns
        -------
        str | None
            'KOSPI' or 'KOSDAQ' ticker used in legacy dataset, or None if unknown.
        """
        with self._session_factory() as session:
            market = session.execute(
                select(Company.market).where(Company.stock_code == stock_code)
            ).scalar_one_or_none()

        if market is None:
            return None
        if market == MarketType.KOSPI:
            return "KOSPI"
        if market == MarketType.KOSDAQ:
            return "KOSDAQ"
        return None
