import enum
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transactions import Transaction, TransactionStatus, TransactionType
from app.models.users import User
from app.queries.timespan_transactions_metrics import (
    TimespanTransactionsMetricsQuery,
    TimespanTransactionsMetricsQueryParams,
)
from app.utils.date import DateRange

from .user_countries import get_user_countries


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
    """Retrieve and aggregate transaction metrics over a specified timespan.

    This service function orchestrates the process of fetching transaction
    analytics. It performs two main queries if necessary:
    1. An "overall" query to get the total, average, min, and max values
       for the entire specified date range.
    2. A "daily" query to get a day-by-day breakdown of metrics, including
       the percentage change from the previous day for each metric.

    Args:
        db: The asynchronous database session.
        date_range: The start and end dates for the report.
        status: Optional filter for transaction status.
        type: Optional filter for transaction type.
        include_avg: Whether to include the average transaction sum.
        include_min: Whether to include the minimum transaction sum.
        include_max: Whether to include the maximum transaction sum.
        include_daily_shift: Whether to include the daily metrics breakdown.

    Returns:
        A TimespanTransactionsMetrics object containing the aggregated data.
        If query parameters are invalid (e.g., requesting metrics for 'failed'
        status without specifying avg, min, or max), it returns a
        zeroed/nulled metrics object.
    """
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


class ReportByCountriesSort(str, enum.Enum):
    COUNT = "count"
    TOTAL = "total"
    AVG = "avg"


@dataclass
class ReportByCountryItem:
    country: str
    count: int
    total: Decimal
    avg: Decimal


async def get_report_by_countries(
    db: AsyncSession, sort_by: ReportByCountriesSort | None = None, top_n: int | None = None
) -> list[ReportByCountryItem]:
    """
    Get report by country.

    Args:
        db: Database session.
        sort_by: Sort by total, count, or avg.
        top_n: Top n countries.

    Uses user_countries service to get user countries.

    Returns:
        aggregated metrics by user countries.
    """
    dataframe = get_user_countries()

    user_ids = dataframe["id"].tolist()

    if not user_ids:
        return []

    dataframe["count"] = 0
    dataframe["total"] = 0.0
    dataframe["avg"] = 0.0

    user_transactions_result = await db.execute(
        select(
            User.external_id,
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.sum).label("total"),
            func.avg(Transaction.sum).label("avg"),
        )
        .join(User.transactions)
        .where(User.external_id.in_(user_ids))
        .group_by(User.external_id)
    )

    for user_eid, count, total, avg in user_transactions_result:
        dataframe.loc[dataframe["id"] == user_eid, ["count", "total", "avg"]] = [count, total, avg]

    dataframe = dataframe.groupby("country", as_index=False).agg(
        count=("count", "sum"),
        total=("total", "sum"),
        avg=("avg", "mean"),
    )

    if sort_by:
        dataframe = dataframe.sort_values(by=sort_by.value, ascending=False)

    if top_n:
        dataframe = dataframe.head(top_n)

    result = list(map(lambda x: ReportByCountryItem(**x), dataframe.to_dict(orient="records")))

    return result
