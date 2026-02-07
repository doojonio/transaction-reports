import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, text
from sqlalchemy.dialects.postgresql import NUMERIC, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import User


class TransactionStatus(str, enum.Enum):
    SUCCESSFULL = "successfull"
    FAILED = "failed"


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    INVOICE = "invoice"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    sum: Mapped[Decimal] = mapped_column(NUMERIC)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship("User", back_populates="transactions")
