from __future__ import annotations

import enum
import datetime as dt

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKeyConstraint,
    Integer,
    String,
    BigInteger,
)
from sqlalchemy.dialects.mysql import CHAR, DECIMAL, TINYINT, VARCHAR
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MarketType(enum.Enum):
    """Market type enum for Company.market."""
    KOSPI = 1
    KOSDAQ = 2
    KONEX = 3
    OTHERS = 4


class CreditRating(Base):
    """credit_rating table."""

    __tablename__ = "credit_rating"

    bond_type_code = Column(CHAR(2), primary_key=True)
    credit_rating_code = Column(CHAR(7), primary_key=True)
    credit_rating_name = Column(String(15), nullable=False)
    credit_rating_value = Column(String(5), nullable=False)


class BondYTM(Base):
    """bond_ytm table (KIS)."""

    __tablename__ = "bond_ytm"

    bond_type_code = Column(CHAR(2), primary_key=True)
    credit_rating_date = Column(Date, primary_key=True)
    credit_rating_code = Column(CHAR(7), primary_key=True)

    m3 = Column(DECIMAL(8, 5))
    m6 = Column(DECIMAL(8, 5))
    m9 = Column(DECIMAL(8, 5))
    y1 = Column(DECIMAL(8, 5))
    y15a = Column(DECIMAL(8, 5))
    y2 = Column(DECIMAL(8, 5))
    y25 = Column(DECIMAL(8, 5))
    y3 = Column(DECIMAL(8, 5))
    y5 = Column(DECIMAL(8, 5))
    y7 = Column(DECIMAL(8, 5))
    y10 = Column(DECIMAL(8, 5))
    y15 = Column(DECIMAL(8, 5))
    y20 = Column(DECIMAL(8, 5))
    y30 = Column(DECIMAL(8, 5))
    y50 = Column(DECIMAL(8, 5))

    __table_args__ = (
        ForeignKeyConstraint(
            ["bond_type_code", "credit_rating_code"],
            ["credit_rating.bond_type_code", "credit_rating.credit_rating_code"],
            onupdate="CASCADE",
        ),
    )


class BondYTMFNP(Base):
    """fnp_bond_ytm table (FNP)."""

    __tablename__ = "fnp_bond_ytm"

    bond_type_code = Column(CHAR(2), primary_key=True)
    credit_rating_date = Column(Date, primary_key=True)
    credit_rating_code = Column(CHAR(7), primary_key=True)

    m3 = Column(DECIMAL(8, 5))
    m6 = Column(DECIMAL(8, 5))
    m9 = Column(DECIMAL(8, 5))
    y1 = Column(DECIMAL(8, 5))
    y15a = Column(DECIMAL(8, 5))
    y2 = Column(DECIMAL(8, 5))
    y25 = Column(DECIMAL(8, 5))
    y3 = Column(DECIMAL(8, 5))
    y4 = Column(DECIMAL(8, 5))
    y5 = Column(DECIMAL(8, 5))
    y7 = Column(DECIMAL(8, 5))
    y10 = Column(DECIMAL(8, 5))
    y15 = Column(DECIMAL(8, 5))
    y20 = Column(DECIMAL(8, 5))
    y30 = Column(DECIMAL(8, 5))
    y50 = Column(DECIMAL(8, 5))

    __table_args__ = (
        ForeignKeyConstraint(
            ["bond_type_code", "credit_rating_code"],
            ["credit_rating.bond_type_code", "credit_rating.credit_rating_code"],
            onupdate="CASCADE",
        ),
    )


class TreasuryBondYTM(Base):
    """treasury_bond_ytm table."""

    __tablename__ = "treasury_bond_ytm"

    credit_rating_date = Column(Date, primary_key=True)

    m3 = Column(DECIMAL(8, 5))
    m6 = Column(DECIMAL(8, 5))
    m9 = Column(DECIMAL(8, 5))
    y1 = Column(DECIMAL(8, 5))
    y15a = Column(DECIMAL(8, 5))
    y2 = Column(DECIMAL(8, 5))
    y25 = Column(DECIMAL(8, 5))
    y3 = Column(DECIMAL(8, 5))
    y4 = Column(DECIMAL(8, 5))
    y5 = Column(DECIMAL(8, 5))
    y7 = Column(DECIMAL(8, 5))
    y10 = Column(DECIMAL(8, 5))
    y15 = Column(DECIMAL(8, 5))
    y20 = Column(DECIMAL(8, 5))
    y30 = Column(DECIMAL(8, 5))
    y50 = Column(DECIMAL(8, 5))


class StockPrice(Base):
    """stock_price table (subset used by infra)."""

    __tablename__ = "stock_price"

    price_date = Column(Date, primary_key=True)
    stock_code = Column(VARCHAR(6), primary_key=True)

    open_price = Column(Integer)
    high_price = Column(Integer)
    low_price = Column(Integer)
    close_price = Column(Integer)
    adj_close_price = Column(Integer)
    volume = Column(BigInteger)

    last_updated = Column(DateTime, default=dt.datetime.now)
    create_date = Column(DateTime, default=dt.datetime.now)


class Company(Base):
    """company table (subset used by infra)."""

    __tablename__ = "company"

    stock_code = Column(CHAR(6), primary_key=True)
    market = Column(SAEnum(MarketType), nullable=False)

    corp_name = Column(String(50), nullable=False)
    category = Column(String(50))
    business = Column(String(150))
    listing_date = Column(Date)
    fiscal_month = Column(TINYINT)

    ceo_name = Column(String(50))
    url = Column(String(150))
    province = Column(String(30))

    last_updated = Column(DateTime, default=dt.datetime.now, onupdate=dt.datetime.now)
    create_date = Column(DateTime, default=dt.datetime.now)
