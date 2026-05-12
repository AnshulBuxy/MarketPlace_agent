from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin
from .enums import MessageType


class InboundMessage(UUIDMixin, TimestampMixin, Base):
    """Inbound WhatsApp message payload."""

    __tablename__ = "inbound_messages"

    message_sid: Mapped[str | None] = mapped_column(String(64))
    from_number: Mapped[str] = mapped_column(String(32), index=True)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, native_enum=False),
        nullable=False,
    )
    num_media: Mapped[int] = mapped_column(Integer, default=0)
    media_urls: Mapped[list[dict] | None] = mapped_column(JSON)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    artisan_id: Mapped[UUID | None] = mapped_column(ForeignKey("artisans.id"))
    artisan = relationship("Artisan", back_populates="messages")
