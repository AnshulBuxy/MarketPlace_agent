from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ConversationSession(TimestampMixin, Base):
	"""Conversation state per phone number."""

	__tablename__ = "conversation_sessions"

	phone_number: Mapped[str] = mapped_column(String(64), primary_key=True)
	language: Mapped[str] = mapped_column(String(16), default="english", nullable=False)
	pending_action: Mapped[str | None] = mapped_column(String(64))
	product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))
	state_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
