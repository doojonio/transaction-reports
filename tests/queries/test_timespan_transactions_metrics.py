from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.models.transactions import TransactionStatus, TransactionType
from app.queries.timespan_transactions_metrics import (
    MetricsItem,
    TimespanTransactionsMetricsQuery,
    TimespanTransactionsMetricsQueryParams,
    _decimal_or_none,
)
from app.utils.date import DateRange
from tests.factories import TransactionFactory, UserFactory


class TestTimespanTransactionsMetricsQueryParams:
    def test_create_valid_params(self):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31))
        )
        assert params.date_range.start_date == date(2024, 1, 1)
        assert params.date_range.end_date == date(2024, 12, 31)
        assert params.status is None
        assert params.type is None
        assert params.include_avg is False
        assert params.include_min is False
        assert params.include_max is False
        assert params.include_daily_shift is False

    def test_create_with_all_params(self):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.PAYMENT,
            include_avg=True,
            include_min=True,
            include_max=True,
            include_daily_shift=True,
        )
        assert params.status == TransactionStatus.SUCCESSFULL
        assert params.type == TransactionType.PAYMENT
        assert params.include_avg is True
        assert params.include_min is True
        assert params.include_max is True
        assert params.include_daily_shift is True

    def test_failed_status_without_aggregates_raises_error(self):
        with pytest.raises(
            ValueError,
            match=(
                "At least one of include_avg, include_min, include_max must be True "
                "when status is FAILED"
            ),
        ):
            TimespanTransactionsMetricsQueryParams(
                date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
                status=TransactionStatus.FAILED,
            )

    def test_failed_status_with_avg_is_valid(self):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
            status=TransactionStatus.FAILED,
            include_avg=True,
        )
        assert params.status == TransactionStatus.FAILED

    def test_failed_status_with_min_is_valid(self):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
            status=TransactionStatus.FAILED,
            include_min=True,
        )
        assert params.status == TransactionStatus.FAILED

    def test_failed_status_with_max_is_valid(self):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
            status=TransactionStatus.FAILED,
            include_max=True,
        )
        assert params.status == TransactionStatus.FAILED


class TestMetricsItem:
    def test_create_metrics_item(self):
        item = MetricsItem(
            sum_total=Decimal("1000.50"),
            sum_avg=Decimal("250.12"),
            sum_min=Decimal("100.00"),
            sum_max=Decimal("500.00"),
            date=date(2024, 1, 15),
            sum_total_daily_shift=Decimal("5.5"),
            sum_avg_daily_shift=Decimal("2.3"),
            sum_min_daily_shift=Decimal("-1.2"),
            sum_max_daily_shift=Decimal("10.0"),
        )
        assert item.sum_total == Decimal("1000.50")
        assert item.sum_avg == Decimal("250.12")
        assert item.sum_min == Decimal("100.00")
        assert item.sum_max == Decimal("500.00")
        assert item.date == date(2024, 1, 15)
        assert item.sum_total_daily_shift == Decimal("5.5")
        assert item.sum_avg_daily_shift == Decimal("2.3")
        assert item.sum_min_daily_shift == Decimal("-1.2")
        assert item.sum_max_daily_shift == Decimal("10.0")

    def test_create_metrics_item_with_none_values(self):
        item = MetricsItem(
            sum_total=Decimal("1000.50"),
            sum_avg=None,
            sum_min=None,
            sum_max=None,
            date=None,
            sum_total_daily_shift=None,
            sum_avg_daily_shift=None,
            sum_min_daily_shift=None,
            sum_max_daily_shift=None,
        )
        assert item.sum_total == Decimal("1000.50")
        assert item.sum_avg is None
        assert item.sum_min is None
        assert item.sum_max is None
        assert item.date is None
        assert item.sum_total_daily_shift is None


class TestDecimalOrNone:
    def test_none_returns_none(self):
        assert _decimal_or_none(None) is None

    def test_decimal_returns_decimal(self):
        assert _decimal_or_none(Decimal("123.45")) == Decimal("123.45")

    def test_int_converts_to_decimal(self):
        assert _decimal_or_none(100) == Decimal("100")

    def test_float_converts_to_decimal(self):
        result = _decimal_or_none(123.45)
        assert result is not None
        assert abs(result - Decimal("123.45")) < Decimal("0.01")

    def test_string_converts_to_decimal(self):
        assert _decimal_or_none("456.78") == Decimal("456.78")


class TestTimespanTransactionsMetricsQuery:
    async def test_basic_query_returns_total(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31))
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("300.00")
        assert results[0].sum_avg is None
        assert results[0].sum_min is None
        assert results[0].sum_max is None
        assert results[0].date is None

    async def test_query_with_avg(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), include_avg=True
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("300.00")
        assert results[0].sum_avg == Decimal("100.00")

    async def test_query_with_min(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("50.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("150.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), include_min=True
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_min == Decimal("50.00")

    async def test_query_with_max(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("50.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("150.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), include_max=True
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_max == Decimal("150.00")

    async def test_filter_by_status(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user, sum=Decimal("200.00"), status=TransactionStatus.FAILED, created_at=base_date
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            status=TransactionStatus.SUCCESSFULL,
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("100.00")

    async def test_filter_by_type(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.PAYMENT,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.INVOICE,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), type=TransactionType.PAYMENT
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("100.00")

    async def test_filter_by_date_range(self, db):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 2, 15, 12, 0, 0),
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31))
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("100.00")

    async def test_daily_shift_groups_by_date(self, db):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 16, 12, 0, 0),
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), include_daily_shift=True
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 2
        assert results[0].date == date(2024, 1, 15)
        assert results[0].sum_total == Decimal("100.00")
        assert results[1].date == date(2024, 1, 16)
        assert results[1].sum_total == Decimal("200.00")

    async def test_daily_shift_calculates_percentage_change(self, db):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("150.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 16, 12, 0, 0),
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)), include_daily_shift=True
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 2
        assert results[0].sum_total_daily_shift is None
        assert results[1].sum_total_daily_shift == Decimal("50.00")

    async def test_failed_status_excludes_total(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user, sum=Decimal("100.00"), status=TransactionStatus.FAILED, created_at=base_date
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            status=TransactionStatus.FAILED,
            include_avg=True,
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("0")
        assert results[0].sum_avg == Decimal("100.00")

    async def test_empty_result_set(self, db):
        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31))
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("0")
        assert results[0].sum_avg is None
        assert results[0].sum_min is None
        assert results[0].sum_max is None

    async def test_multiple_transactions_same_day(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date + timedelta(hours=2),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("300.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date + timedelta(hours=4),
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            include_avg=True,
            include_min=True,
            include_max=True,
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("600.00")
        assert results[0].sum_avg == Decimal("200.00")
        assert results[0].sum_min == Decimal("100.00")
        assert results[0].sum_max == Decimal("300.00")

    async def test_only_successful_transactions_count_for_total(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user, sum=Decimal("200.00"), status=TransactionStatus.FAILED, created_at=base_date
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31))
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("100.00")

    async def test_avg_daily_shift_requires_both_flags(self, db):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            include_avg=True,
            include_daily_shift=False,
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_avg_daily_shift is None

    async def test_combined_filters(self, db):
        base_date = datetime(2024, 1, 15, 12, 0, 0)
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.PAYMENT,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.INVOICE,
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("300.00"),
            status=TransactionStatus.FAILED,
            type=TransactionType.PAYMENT,
            created_at=base_date,
        )

        params = TimespanTransactionsMetricsQueryParams(
            date_range=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.PAYMENT,
        )
        query = TimespanTransactionsMetricsQuery(db, params)

        results = [item async for item in query]

        assert len(results) == 1
        assert results[0].sum_total == Decimal("100.00")
