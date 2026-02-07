from datetime import date
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query

from app.cache import Cache, get_cache
from app.db import AsyncSession, get_async_session
from app.models.transactions import TransactionStatus, TransactionType
from app.queries.timespan_transactions import (
    TimespanTransactionsQuery,
    TimespanTransactionsQueryParams,
)
from app.schemas.report import ReportSchemaIn, ReportSchemaOut, ReportTransactionSchema

router = APIRouter(prefix="/report", tags=["report"])


@router.get("")
async def get_report(
    params: Annotated[ReportSchemaIn, Query()],
    db: AsyncSession = Depends(get_async_session),
    redis: Cache = Depends(get_cache),
):
    query_params = _build_query_params(params)
    query = TimespanTransactionsQuery(db, query_params)

    avg = None
    min = None
    max = None
    daily_shift = None
    transactions = []

    async for res in query:
        avg = res["sum_avg"]
        min = res["sum_min"]
        max = res["sum_max"]
        daily_shift = "TODO"
        transaction = res["Transaction"]

        transactions.append(ReportTransactionSchema.model_validate(transaction))

    return ReportSchemaOut(
        transactions=transactions,
        avg=avg,
        min=min,
        max=max,
        daily_shift=daily_shift,
    )


def _build_query_params(params: ReportSchemaIn):
    start_date, end_date = params.start_date, params.end_date
    if start_date is None:
        start_date = date.today() + relativedelta(months=-1)
    if end_date is None:
        end_date = date.today()

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be less than end_date")

    status = None
    if params.status != "all":
        status = TransactionStatus(params.status)

    type_ = None
    if params.type != "all":
        type_ = TransactionType(params.type)

    return TimespanTransactionsQueryParams(
        start_date=start_date,
        end_date=end_date,
        status=status,
        type=type_,
        include_avg=params.include_avg,
        include_min=params.include_min,
        include_max=params.include_max,
        include_daily_shift=params.include_daily_shift,
    )
