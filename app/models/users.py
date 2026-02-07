import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .transactions import Transaction


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    first_name: Mapped[str] = mapped_column(String(), nullable=False)
    last_name: Mapped[str] = mapped_column(String(), nullable=False)
    email: Mapped[str] = mapped_column(String(), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=datetime.now(),
        onupdate=datetime.now(),
        nullable=False,
        server_default=text("now()"),
    )

    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
