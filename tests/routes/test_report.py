from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.cache import get_cache
from app.models.transactions import TransactionStatus, TransactionType
from main import app
from tests.factories import TransactionFactory, UserFactory


@pytest.fixture
async def mock_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
async def client(mock_redis):
    app.dependency_overrides[get_cache] = lambda: mock_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestGetReport:
    async def test_basic_report_with_defaults(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2025, 1, 15, 12, 0, 0),
        )

        response = await client.get(
            "/report",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert Decimal(data["total"]) == Decimal("100.00")

    async def test_report_with_date_range(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2024, 1, 15, 12, 0, 0),
        )

        response = await client.get(
            "/report",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total"]) == Decimal("200.00")

    async def test_report_with_avg_min_max(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2025, 2, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2025, 2, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("150.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2025, 2, 15, 12, 0, 0),
        )

        response = await client.get(
            "/report",
            params={
                "start_date": "2025-02-01",
                "end_date": "2025-02-28",
                "status": "all",
                "type": "all",
                "include_avg": True,
                "include_min": True,
                "include_max": True,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total"]) == Decimal("450.00")
        assert Decimal(data["avg"]) == Decimal("150.00")
        assert Decimal(data["min"]) == Decimal("100.00")
        assert Decimal(data["max"]) == Decimal("200.00")

    async def test_report_with_daily_shift(self, client, db, mock_redis):
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

        response = await client.get(
            "/report",
            params={
                "start_date": "2024-01-15",
                "end_date": "2024-01-16",
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["daily"] is not None
        assert len(data["daily"]) == 2
        assert data["daily"][0]["date"] == "2024-01-15"
        assert Decimal(data["daily"][0]["total"]) == Decimal("100.00")
        assert data["daily"][1]["date"] == "2024-01-16"
        assert Decimal(data["daily"][1]["total"]) == Decimal("200.00")

    async def test_report_filter_by_status(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime(2025, 3, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.FAILED,
            created_at=datetime(2025, 3, 15, 12, 0, 0),
        )

        response = await client.get(
            "/report",
            params={
                "start_date": "2025-03-01",
                "end_date": "2025-03-31",
                "status": "successfull",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total"]) == Decimal("100.00")

    async def test_report_filter_by_type(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.PAYMENT,
            created_at=datetime(2025, 4, 15, 12, 0, 0),
        )
        await TransactionFactory(
            user=user,
            sum=Decimal("200.00"),
            status=TransactionStatus.SUCCESSFULL,
            type=TransactionType.INVOICE,
            created_at=datetime(2025, 4, 15, 12, 0, 0),
        )

        response = await client.get(
            "/report",
            params={
                "start_date": "2025-04-01",
                "end_date": "2025-04-30",
                "status": "all",
                "type": "payment",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total"]) == Decimal("100.00")

    async def test_report_invalid_date_range(self, client, db, mock_redis):
        response = await client.get(
            "/report",
            params={
                "start_date": "2024-12-31",
                "end_date": "2024-01-01",
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 400
        assert "start_date must be less than end_date" in response.json()["detail"]

    async def test_report_uses_cache(self, client, db, mock_redis):
        mock_redis.get = AsyncMock(
            return_value='{"total": "500.00", "avg": null, "min": null, "max": null, "daily": null}'
        )
        response = await client.get(
            "/report",
            params={
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total"]) == Decimal("500.00")
        mock_redis.get.assert_called_once()

    async def test_report_sets_cache(self, client, db, mock_redis):
        user = await UserFactory()
        await TransactionFactory(
            user=user,
            sum=Decimal("100.00"),
            status=TransactionStatus.SUCCESSFULL,
            created_at=datetime.now(),
        )

        response = await client.get(
            "/report",
            params={
                "status": "all",
                "type": "all",
                "include_avg": False,
                "include_min": False,
                "include_max": False,
                "include_daily_shift": False,
            },
        )

        assert response.status_code == 200
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 60


class TestGetReportByCountry:
    async def test_basic_report_by_country(self, client, db, mock_redis):
        user1 = await UserFactory(external_id=1001)
        user2 = await UserFactory(external_id=1002)

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

        response = await client.get("/report/by-country")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_report_by_country_with_sort_by_total(self, client, db, mock_redis):
        user1 = await UserFactory(external_id=2001)
        user2 = await UserFactory(external_id=2002)

        await TransactionFactory(user=user1, sum=Decimal("500.00"))
        await TransactionFactory(user=user2, sum=Decimal("100.00"))

        response = await client.get("/report/by-country", params={"sort_by": "total"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

    async def test_report_by_country_with_top_n(self, client, db, mock_redis):
        user1 = await UserFactory(external_id=3001)
        user2 = await UserFactory(external_id=3002)
        user3 = await UserFactory(external_id=3003)

        await TransactionFactory(user=user1, sum=Decimal("100.00"))
        await TransactionFactory(user=user2, sum=Decimal("200.00"))
        await TransactionFactory(user=user3, sum=Decimal("300.00"))

        response = await client.get("/report/by-country", params={"top_n": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2

    async def test_report_by_country_sets_cache(self, client, db, mock_redis):
        user = await UserFactory(external_id=4001)
        await TransactionFactory(user=user, sum=Decimal("100.00"))

        response = await client.get("/report/by-country")

        assert response.status_code == 200
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 60
