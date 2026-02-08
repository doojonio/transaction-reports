from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transactions import TransactionStatus, TransactionType
from app.queries.timespan_transactions_metrics import (
    TimespanTransactionsMetricsQuery,
    TimespanTransactionsMetricsQueryParams,
)
from app.utils.date import DateRange


@dataclass
class TimespanTransactionsMetrics:
    @dataclass
    class DailyMetric:
        date: date
        total: Decimal
        avg: Decimal | None
        min: Decimal | None
        max: Decimal | None
        total_shift_rate: Decimal | None
        avg_shift_rate: Decimal | None
        min_shift_rate: Decimal | None
        max_shift_rate: Decimal | None

    total: Decimal
    avg: Decimal | None
    min: Decimal | None
    max: Decimal | None
    daily: list[DailyMetric] | None


async def get_timespan_transactions_metrics(
    db: AsyncSession,
    date_range: DateRange,
    status: TransactionStatus | None = None,
    type: TransactionType | None = None,
    include_avg: bool = False,
    include_min: bool = False,
    include_max: bool = False,
    include_daily_shift: bool = False,
) -> TimespanTransactionsMetrics:
    try:
        query_params = TimespanTransactionsMetricsQueryParams(
            date_range=date_range,
            status=status,
            type=type,
            include_avg=include_avg,
            include_min=include_min,
            include_max=include_max,
            include_daily_shift=False,
        )
    except ValueError:
        return TimespanTransactionsMetrics(Decimal(0), None, None, None, None)

    overall_query = TimespanTransactionsMetricsQuery(db, query_params)
    overall_metrics = await anext(overall_query)

    result_metrics = TimespanTransactionsMetrics(
        total=overall_metrics.sum_total,
        avg=overall_metrics.sum_avg,
        min=overall_metrics.sum_min,
        max=overall_metrics.sum_max,
        daily=None,
    )

    if not include_daily_shift:
        return result_metrics

    result_metrics.daily = []

    daily_query_params = replace(query_params, include_daily_shift=True)
    daily_query = TimespanTransactionsMetricsQuery(db, daily_query_params)
    async for daily_metric in daily_query:
        result_metrics.daily.append(
            TimespanTransactionsMetrics.DailyMetric(
                date=daily_metric.date,  # type: ignore[arg-type]
                total=daily_metric.sum_total,
                avg=daily_metric.sum_avg,
                min=daily_metric.sum_min,
                max=daily_metric.sum_max,
                total_shift_rate=daily_metric.sum_total_daily_shift,
                avg_shift_rate=daily_metric.sum_avg_daily_shift,
                min_shift_rate=daily_metric.sum_min_daily_shift,
                max_shift_rate=daily_metric.sum_max_daily_shift,
            )
        )

    return result_metrics
