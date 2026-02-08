from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ReportSchemaIn(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["successfull", "failed", "all"]
    type: Literal["payment", "invoice", "all"]
    include_avg: bool
    include_min: bool
    include_max: bool
    include_daily_shift: bool


class ReportSchemaOut(BaseModel):
    total: Decimal
    avg: Decimal | None = None
    min: Decimal | None = None
    max: Decimal | None = None
    daily_shift: str | None = None
