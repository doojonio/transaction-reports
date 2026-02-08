from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.transactions import TransactionStatus, TransactionType
from app.services.transaction_reports import (
    ReportByCountriesSort,
    ReportByCountryItem,
    TimespanTransactionsMetrics,
    get_report_by_countries,
    get_timespan_transactions_metrics,
)
from app.utils.date import DateRange
from tests.factories import TransactionFactory, UserFactory


class TestTimespanTransactionsMetrics:
    def test_create_metrics_with_all_fields(self):
        metrics = TimespanTransactionsMetrics(
            total=Decimal("1000.00"),
            avg=Decimal("100.00"),
            min=Decimal("50.00"),
            max=Decimal("200.00"),
            daily=None,
        )
        assert metrics.total == Decimal("1000.00")
        assert metrics.avg == Decimal("100.00")
        assert metrics.min == Decimal("50.00")
        assert metrics.max == Decimal("200.00")
        assert metrics.daily is None

    def test_create_metrics_with_daily_data(self):
        daily_metric = TimespanTransactionsMetrics.DailyMetric(
            date=date(2024, 1, 15),
            total=Decimal("500.00"),
            avg=Decimal("100.00"),
            min=Decimal("50.00"),
            max=Decimal("150.00"),
            total_shift_rate=Decimal("10.5"),
            avg_shift_rate=Decimal("5.2"),
            min_shift_rate=Decimal("-2.1"),
            max_shift_rate=Decimal("8.3"),
        )

        metrics = TimespanTransactionsMetrics(
            total=Decimal("1000.00"),
            avg=Decimal("100.00"),
            min=Decimal("50.00"),
            max=Decimal("200.00"),
            daily=[daily_metric],
        )

        assert len(metrics.daily) == 1
        assert metrics.daily[0].date == date(2024, 1, 15)
        assert metrics.daily[0].total == Decimal("500.00")
        assert metrics.daily[0].total_shift_rate == Decimal("10.5")

    def test_daily_metric_with_none_values(self):
        daily_metric = TimespanTransactionsMetrics.DailyMetric(
            date=date(2024, 1, 15),
            total=Decimal("500.00"),
            avg=None,
            min=None,
            max=None,
            total_shift_rate=None,
            avg_shift_rate=None,
            min_shift_rate=None,
            max_shift_rate=None,
        )

        assert daily_metric.avg is None
        assert daily_metric.min is None
        assert daily_metric.max is None


class TestGetTimespanTransactionsMetrics:
    async def test_basic_metrics_without_daily_shift(self, db):
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
            created_at=base_date,
        )

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(db, date_range)

        assert result.total == Decimal("300.00")
        assert result.avg is None
        assert result.min is None
        assert result.max is None
        assert result.daily is None

    async def test_metrics_with_avg_min_max(self, db):
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
            created_at=base_date,
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("150.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=base_date,
        )

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(
            db,
            date_range,
            include_avg=True,
            include_min=True,
            include_max=True,
        )

        assert result.total == Decimal("450.00")
        assert result.avg == Decimal("150.00")
        assert result.min == Decimal("100.00")
        assert result.max == Decimal("200.00")
        assert result.daily is None

    async def test_metrics_with_daily_shift(self, db):
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

        date_range = DateRange(date(2024, 1, 15), date(2024, 1, 16))
        result = await get_timespan_transactions_metrics(db, date_range, include_daily_shift=True)

        assert result.total == Decimal("300.00")
        assert result.daily is not None
        assert len(result.daily) == 2
        assert result.daily[0].date == date(2024, 1, 15)
        assert result.daily[0].total == Decimal("100.00")
        assert result.daily[1].date == date(2024, 1, 16)
        assert result.daily[1].total == Decimal("200.00")

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
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.FAILED,
            created_at=base_date,
        )

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(
            db,
            date_range,
            status=TransactionStatus.SUCCESSFULL,
        )

        assert result.total == Decimal("100.00")

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

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(
            db,
            date_range,
            type=TransactionType.PAYMENT,
        )

        assert result.total == Decimal("100.00")

    async def test_invalid_params_returns_zero_metrics(self, db):
        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(
            db,
            date_range,
            status=TransactionStatus.FAILED,
        )

        assert result.total == Decimal("0")
        assert result.avg is None
        assert result.min is None
        assert result.max is None
        assert result.daily is None

    async def test_empty_result_set(self, db):
        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 31))
        result = await get_timespan_transactions_metrics(db, date_range)

        assert result.total == Decimal("0")
        assert result.avg is None
        assert result.min is None
        assert result.max is None
        assert result.daily is None


class TestReportByCountriesSort:
    def test_enum_values(self):
        assert ReportByCountriesSort.COUNT.value == "count"
        assert ReportByCountriesSort.TOTAL.value == "total"
        assert ReportByCountriesSort.AVG.value == "avg"


class TestReportByCountryItem:
    def test_create_item(self):
        item = ReportByCountryItem(
            country="Germany",
            count=10,
            total=Decimal("1000.00"),
            avg=Decimal("100.00"),
        )
        assert item.country == "Germany"
        assert item.count == 10
        assert item.total == Decimal("1000.00")
        assert item.avg == Decimal("100.00")


class TestGetReportByCountries:
    async def test_returns_list_of_country_items(self, db):
        user1 = await UserFactory(external_id=10001)
        user2 = await UserFactory(external_id=10002)

        await TransactionFactory(
            user=user1,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
        )
        await TransactionFactory(
            user=user2,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
        )

        result = await get_report_by_countries(db)

        assert isinstance(result, list)
        assert all(isinstance(item, ReportByCountryItem) for item in result)

    async def test_sort_by_count(self, db):
        user1 = await UserFactory(external_id=201)
        user2 = await UserFactory(external_id=202)
        user3 = await UserFactory(external_id=203)

        await TransactionFactory(user=user1, sum=Decimal("100.00"))
        await TransactionFactory(user=user1, sum=Decimal("100.00"))
        await TransactionFactory(user=user2, sum=Decimal("200.00"))
        await TransactionFactory(user=user3, sum=Decimal("300.00"))

        result = await get_report_by_countries(db, sort_by=ReportByCountriesSort.COUNT)

        assert len(result) > 0
        if len(result) > 1:
            assert result[0].count >= result[1].count

    async def test_sort_by_total(self, db):
        user1 = await UserFactory(external_id=301)
        user2 = await UserFactory(external_id=302)

        await TransactionFactory(user=user1, sum=Decimal("500.00"))
        await TransactionFactory(user=user2, sum=Decimal("100.00"))

        result = await get_report_by_countries(db, sort_by=ReportByCountriesSort.TOTAL)

        assert len(result) > 0
        if len(result) > 1:
            assert result[0].total >= result[1].total

    async def test_sort_by_avg(self, db):
        user1 = await UserFactory(external_id=401)
        user2 = await UserFactory(external_id=402)

        await TransactionFactory(user=user1, sum=Decimal("500.00"))
        await TransactionFactory(user=user2, sum=Decimal("100.00"))

        result = await get_report_by_countries(db, sort_by=ReportByCountriesSort.AVG)

        assert len(result) > 0
        if len(result) > 1:
            assert result[0].avg >= result[1].avg

    async def test_top_n_limit(self, db):
        user1 = await UserFactory(external_id=501)
        user2 = await UserFactory(external_id=502)
        user3 = await UserFactory(external_id=503)

        await TransactionFactory(user=user1, sum=Decimal("100.00"))
        await TransactionFactory(user=user2, sum=Decimal("200.00"))
        await TransactionFactory(user=user3, sum=Decimal("300.00"))

        result = await get_report_by_countries(db, top_n=2)

        assert len(result) <= 2

    async def test_empty_user_ids_returns_empty_list(self, db):
        with patch("app.services.transaction_reports.get_user_countries") as mock:
            mock.return_value = MagicMock(
                __getitem__=lambda self, key: MagicMock(tolist=lambda: [])
            )

            result = await get_report_by_countries(db)

            assert result == []

    async def test_no_transactions_for_users(self, db):
        await UserFactory(external_id=999)

        result = await get_report_by_countries(db)

        assert isinstance(result, list)
