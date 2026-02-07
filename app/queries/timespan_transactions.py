from dataclasses import dataclass
from datetime import date
from functools import cached_property

from sqlalchemy import and_, func, select

from app.db import AsyncSession
from app.models.transactions import Transaction, TransactionStatus, TransactionType


@dataclass(slots=True, kw_only=True, frozen=True)
class TimespanTransactionsQueryParams:
    start_date: date
    end_date: date
    status: TransactionStatus | None = None
    type: TransactionType | None = None
    include_avg: bool = False
    include_min: bool = False
    include_max: bool = False
    include_daily_shift: bool = False


class TimespanTransactionsQuery:
    def __init__(self, db: AsyncSession, params: TimespanTransactionsQueryParams):
        self._db = db
        self._params = params

        self._query = None
        self._iterator = None

    def _filter_by_date(self):
        return and_(
            func.date(Transaction.created_at) >= self._params.start_date,
            func.date(Transaction.created_at) <= self._params.end_date,
        )

    def _filter_by_status(self):
        if self._params.status is None:
            return None
        return Transaction.status == self._params.status

    def _filter_by_type(self):
        if self._params.type is None:
            return None
        return Transaction.type == self._params.type

    def _build_filters(self):
        filters = []
        for method in [self._filter_by_date, self._filter_by_status, self._filter_by_type]:
            filter_ = method()
            if filter_ is not None:
                filters.append(filter_)

        return and_(*filters)

    def _column_avg(self):
        if not self._params.include_avg or self._params.status == TransactionStatus.FAILED:
            return None

        return (
            func.avg(Transaction.sum)
            .filter(Transaction.status == TransactionStatus.SUCCESSFULL)
            .over()
            .label("sum_avg")
        )

    def _column_min(self):
        if not self._params.include_min or self._params.status == TransactionStatus.FAILED:
            return None

        return (
            func.min(Transaction.sum)
            .filter(Transaction.status == TransactionStatus.SUCCESSFULL)
            .over()
            .label("sum_min")
        )

    def _column_max(self):
        if not self._params.include_max or self._params.status == TransactionStatus.FAILED:
            return None

        return (
            func.max(Transaction.sum)
            .filter(Transaction.status == TransactionStatus.SUCCESSFULL)
            .over()
            .label("sum_max")
        )

    # TODO: add daily shift
    def _column_daily_shift(self):
        if not self._params.include_daily_shift:
            return None

        return func.date(Transaction.created_at).label("daily_shift")

    def _build_columns(self):
        columns = []
        for method in [
            self._column_avg,
            self._column_min,
            self._column_max,
            self._column_daily_shift,
        ]:
            column = method()
            if column is None:
                continue
            columns.append(column)

        return columns

    @cached_property
    def _stmt(self):
        return select(Transaction, *self._build_columns()).where(self._build_filters())

    async def _execute_stmt(self):
        return await self._db.execute(self._stmt)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._query is None:
            self._query = await self._execute_stmt()
            self._iterator = iter(self._query.mappings())

        try:
            return next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration
