from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Query
from pydantic import BaseModel

from valuation_engine.services.spotrate_service import SpotrateService, SpotrateRequest

router = APIRouter(prefix="/spotrate", tags=["spotrate"])


class SpotrateOut(BaseModel):
    used_corp_date: dt.date
    used_treasury_date: dt.date
    rows: list[dict]


@router.get("", response_model=SpotrateOut)
def get_spotrate(
    base_date: dt.date = Query(...),
    maturity_date: dt.date = Query(...),
    credit_rating: str = Query(...),
    data_source: str = Query("KIS"),
    corp_bond_type_code: str = Query("CB"),
    ytm_limit_years: int = Query(15, ge=1, le=50),
):
    svc = SpotrateService()
    res = svc.build_spotrate(
        SpotrateRequest(
            base_date=base_date,
            maturity_date=maturity_date,
            credit_rating=credit_rating,
            data_source=data_source,
            corp_bond_type_code=corp_bond_type_code,
            ytm_limit_years=ytm_limit_years,
        )
    )

    # quick JSON serialization (pandas → list[dict])
    rows = res.curve.to_dict(orient="records")
    return SpotrateOut(
        used_corp_date=res.used_corp_date,
        used_treasury_date=res.used_treasury_date,
        rows=rows,
    )
