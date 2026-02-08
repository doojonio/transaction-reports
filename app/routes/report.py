from datetime import date
from typing import Annotated

from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import Cache, get_cache
from app.db import get_async_session
from app.models.transactions import TransactionStatus, TransactionType
from app.policies.cache import REPORT_CACHE_TTL_SECONDS
from app.schemas.report import ReportSchemaIn, ReportSchemaOut
from app.services import transaction_reports
from app.utils.date import DateRange

router = APIRouter(prefix="/report", tags=["report"])


@router.get("", response_model=ReportSchemaOut, response_model_exclude_none=True)
async def get_report(
    params: Annotated[ReportSchemaIn, Query()],
    db: AsyncSession = Depends(get_async_session),
    redis: Cache = Depends(get_cache),
) -> ReportSchemaOut:
    start_date, end_date = params.start_date, params.end_date
    if start_date is None:
        start_date = date.today() + relativedelta(months=-1)
    if end_date is None:
        end_date = date.today()

    try:
        date_range = DateRange(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])

    status = None
    if params.status != "all":
        status = TransactionStatus(params.status)

    type_ = None
    if params.type != "all":
        type_ = TransactionType(params.type)

    cache_key = params.cache_key
    cached_metrics = await redis.get(cache_key)
    if cached_metrics:
        return ReportSchemaOut.model_validate_json(cached_metrics)

    metrics = await transaction_reports.get_timespan_transactions_metrics(
        db,
        date_range,
        status,
        type_,
        params.include_avg,
        params.include_min,
        params.include_max,
        params.include_daily_shift,
    )

    model = ReportSchemaOut.model_validate(metrics)
    await redis.set(cache_key, model.model_dump_json(), ex=REPORT_CACHE_TTL_SECONDS)
    return model
