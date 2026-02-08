from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transactions import TransactionStatus, TransactionType
from app.queries.timespan_transactions_metrics import (
    MetricsItem,
    TimespanTransactionsMetricsQuery,
    TimespanTransactionsMetricsQueryParams,
)
from app.utils.date import DateRange


async def get_timespan_transactions_metrics(
    db: AsyncSession,
    date_range: DateRange,
    status: TransactionStatus | None = None,
    type: TransactionType | None = None,
    include_avg: bool = False,
    include_min: bool = False,
    include_max: bool = False,
    include_daily_shift: bool = False,
) -> list[MetricsItem]:
    query_params = TimespanTransactionsMetricsQueryParams(
        date_range=date_range,
        status=status,
        type=type,
        include_avg=include_avg,
        include_min=include_min,
        include_max=include_max,
        include_daily_shift=include_daily_shift,
    )
    query = TimespanTransactionsMetricsQuery(db, query_params)

    results = []
    async for res in query:
        results.append(res)

    return results
