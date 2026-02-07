import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.models.transactions import TransactionStatus, TransactionType


class ReportSchemaIn(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    status: Literal[str(TransactionStatus.SUCCESSFULL), str(TransactionStatus.FAILED), "all"]
    type: Literal[str(TransactionType.PAYMENT), str(TransactionType.INVOICE), "all"]
    include_avg: bool
    include_min: bool
    include_max: bool
    include_daily_shift: bool


class ReportTransactionSchema(BaseModel):
    id: uuid.UUID
    sum: Decimal
    status: TransactionStatus
    type: TransactionType
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportSchemaOut(BaseModel):
    transactions: list[ReportTransactionSchema]
    avg: Decimal | None = None
    min: Decimal | None = None
    max: Decimal | None = None
    daily_shift: str | None = None
