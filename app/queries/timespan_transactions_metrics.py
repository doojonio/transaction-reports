from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cached_property
from typing import Any, Callable, Iterator, Self

from sqlalchemy import ColumnElement, Result, RowMapping, Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.transactions import Transaction, TransactionStatus, TransactionType
from app.utils.date import DateRange


@dataclass(slots=True, kw_only=True, frozen=True)
class TimespanTransactionsMetricsQueryParams:
    date_range: DateRange
    status: TransactionStatus | None = None
    type: TransactionType | None = None
    include_avg: bool = False
    include_min: bool = False
    include_max: bool = False
    include_daily_shift: bool = False

    def __post_init__(self) -> None:
        """Validate query parameters."""
        if self.status == TransactionStatus.FAILED and not (
            self.include_avg or self.include_min or self.include_max
        ):
            raise ValueError(
                "At least one of include_avg, include_min, include_max must be True "
                + "when status is FAILED"
            )


@dataclass(slots=True, kw_only=True)
class MetricsItem:
    sum_total: Decimal
    sum_avg: Decimal | None
    sum_min: Decimal | None
    sum_max: Decimal | None
    date: date | None
    sum_total_daily_shift: Decimal | None
    sum_avg_daily_shift: Decimal | None
    sum_min_daily_shift: Decimal | None
    sum_max_daily_shift: Decimal | None


class TimespanTransactionsMetricsQuery:
    """Builds and executes a query to get transaction metrics over a timespan.

    This class constructs a dynamic SQL query based on the provided parameters
    to calculate metrics like total, average, minimum, and maximum transaction
    sums. It can also calculate the percentage change of these metrics
    compared to the previous day.

    The class is implemented as an async iterator, yielding MetricsItem objects.
    """

    def __init__(self, db: AsyncSession, params: TimespanTransactionsMetricsQueryParams):
        """Initialize the query builder.

        Args:
            db: The asynchronous database session.
            params: The query parameters object defining filters and metrics.
        """
        self._db = db
        self._params = params

        self._query: Result[Any] | None = None
        self._iterator: Iterator[RowMapping] | None = None

    def _filter_by_date(self) -> ColumnElement[bool]:
        return and_(
            func.date(Transaction.created_at) >= self._params.date_range.start_date,
            func.date(Transaction.created_at) <= self._params.date_range.end_date,
        )

    def _filter_by_status(self) -> ColumnElement[bool] | None:
        if self._params.status is None:
            return None
        return Transaction.status == self._params.status

    def _filter_by_type(self) -> ColumnElement[bool] | None:
        if self._params.type is None:
            return None
        return Transaction.type == self._params.type

    def _build_filters(self) -> ColumnElement[bool]:
        filters = []
        for method in [self._filter_by_date, self._filter_by_status, self._filter_by_type]:
            filter_ = method()
            if filter_ is not None:
                filters.append(filter_)

        return and_(*filters)

    def _column_avg(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_avg:
            return None

        return func.avg(self._cte_filtered_transactions.sum).label("sum_avg")

    def _column_avg_daily_shift(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_avg or not self._params.include_daily_shift:
            return None

        return self._daily_shift(func.avg).label("sum_avg_daily_shift")

    def _column_min(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_min:
            return None

        return func.min(self._cte_filtered_transactions.sum).label("sum_min")

    def _column_min_daily_shift(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_min or not self._params.include_daily_shift:
            return None

        return self._daily_shift(func.min).label("sum_min_daily_shift")

    def _column_max(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_max:
            return None

        return func.max(self._cte_filtered_transactions.sum).label("sum_max")

    def _column_max_daily_shift(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_max or not self._params.include_daily_shift:
            return None

        return self._daily_shift(func.max).label("sum_max_daily_shift")

    def _column_total(self) -> ColumnElement[Decimal] | None:
        if self._params.status == TransactionStatus.FAILED:
            return None

        return (
            func.sum(self._cte_filtered_transactions.sum)
            .filter(self._cte_filtered_transactions.status == TransactionStatus.SUCCESSFULL)
            .label("sum_total")
        )

    def _column_total_daily_shift(self) -> ColumnElement[Decimal] | None:
        if not self._params.include_daily_shift or self._params.status == TransactionStatus.FAILED:
            return None

        return self._daily_shift(func.sum).label("sum_total_daily_shift")

    def _column_date(self) -> ColumnElement[date] | None:
        if not self._params.include_daily_shift:
            return None

        return func.date(self._cte_filtered_transactions.created_at).label("date")

    def _daily_shift(self, agg_func: Callable[[Any], Any]) -> ColumnElement[Decimal]:
        """Calculate the percentage change of an aggregate from the previous day.

        Uses the LAG window function to compare the current day's aggregated
        value with the previous day's value.

        Args:
            agg_func: The SQLAlchemy aggregation function (e.g., func.sum, func.avg).

        Returns:
            A SQLAlchemy ColumnElement representing the percentage change.
        """
        return (  # type: ignore[no-any-return]
            100
            * (
                agg_func(self._cte_filtered_transactions.sum)
                - func.lag(agg_func(self._cte_filtered_transactions.sum)).over(
                    order_by=func.date(self._cte_filtered_transactions.created_at)
                )
            )
            / func.lag(agg_func(self._cte_filtered_transactions.sum)).over(
                order_by=func.date(self._cte_filtered_transactions.created_at)
            )
        )

    def _build_columns(self) -> list[ColumnElement[Any]]:
        columns = []
        for method in [
            self._column_total,
            self._column_avg,
            self._column_min,
            self._column_max,
            # daily shift columns
            self._column_date,
            self._column_total_daily_shift,
            self._column_avg_daily_shift,
            self._column_min_daily_shift,
            self._column_max_daily_shift,
        ]:
            column = method()
            if column is None:
                continue
            columns.append(column)

        return columns

    @cached_property
    def _cte_filtered_transactions(self) -> type[Transaction]:
        """Create a materialized Common Table Expression (CTE) of filtered transactions.

        This CTE pre-filters the transactions based on the date range, status, and
        type specified in the query parameters. Materializing it can improve
        performance as it's accessed multiple times in the main query.

        Returns:
            An aliased Transaction model pointing to the CTE.
        """
        cte = (
            select(Transaction)
            .where(self._build_filters())
            .cte("filtered_transactions")
            .prefix_with("MATERIALIZED")
        )
        return aliased(Transaction, cte)

    @cached_property
    def _stmt(self) -> Select[Any]:
        """Build the final SQLAlchemy SELECT statement.

        This statement selects the columns generated by _build_columns from the
        filtered transactions CTE. If daily shift metrics are included, it
        groups the results by date.

        Returns:
            A SQLAlchemy Select object representing the complete query.
        """
        stmt = select(*self._build_columns()).select_from(self._cte_filtered_transactions)

        if self._params.include_daily_shift:
            date_c = func.date(self._cte_filtered_transactions.created_at)
            stmt = stmt.group_by(date_c).order_by(date_c)

        return stmt

    async def _execute_stmt(self) -> Result[Any]:
        return await self._db.execute(self._stmt)

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> MetricsItem:
        """Execute the query and yield the next result row as a MetricsItem.

        On the first call, it executes the statement and creates an iterator over
        the results (and yields). Subsequent calls yield the next item from the iterator.

        Raises:
            StopAsyncIteration: When there are no more results.

        Returns:
            A MetricsItem dataclass instance for the next result row.
        """
        if self._query is None:
            self._query = await self._execute_stmt()
            self._iterator = iter(self._query.mappings())

        assert self._iterator

        try:
            mapping = next(self._iterator)

            return MetricsItem(
                sum_total=_decimal_or_none(mapping.get("sum_total", 0)) or Decimal(0),
                sum_avg=_decimal_or_none(mapping.get("sum_avg", None)),
                sum_min=_decimal_or_none(mapping.get("sum_min", None)),
                sum_max=_decimal_or_none(mapping.get("sum_max", None)),
                date=mapping.get("date", None),
                sum_total_daily_shift=_decimal_or_none(mapping.get("sum_total_daily_shift", None)),
                sum_avg_daily_shift=_decimal_or_none(mapping.get("sum_avg_daily_shift", None)),
                sum_min_daily_shift=_decimal_or_none(mapping.get("sum_min_daily_shift", None)),
                sum_max_daily_shift=_decimal_or_none(mapping.get("sum_max_daily_shift", None)),
            )
        except StopIteration:
            raise StopAsyncIteration


def _decimal_or_none(value: Any) -> Decimal | None:
    """Convert to decimal or none."""
    if value is None:
        return None
    return Decimal(value)
