from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AuditEvent(UUIDMixin, TimestampMixin, Base):
	"""Audit log entry."""

	__tablename__ = "audit_events"

	agent: Mapped[str] = mapped_column(String(80))
	action: Mapped[str] = mapped_column(String(120))
	input_data: Mapped[dict | None] = mapped_column(JSON)
	output_data: Mapped[dict | None] = mapped_column(JSON)
	product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))
