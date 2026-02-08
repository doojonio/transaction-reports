from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportSchemaIn(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["successfull", "failed", "all"]
    type: Literal["payment", "invoice", "all"]
    include_avg: bool
    include_min: bool
    include_max: bool
    include_daily_shift: bool

    @property
    def cache_key(self) -> str:
        """Generate cache key."""
        return (
            f"report_{self.start_date}_{self.end_date}_{self.status}"
            + f"_{self.type}_{self.include_avg}_{self.include_min}_"
            + f"{self.include_max}_{self.include_daily_shift}"
        )


class ReportSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class DailyMetric(BaseModel):
        model_config = ConfigDict(from_attributes=True)

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
