from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class WorkflowRun(TimestampMixin, Base):
	"""Persisted workflow state for history and debugging."""

	__tablename__ = "workflow_runs"

	workflow_id: Mapped[str] = mapped_column(String(64), primary_key=True)
	status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
	current_node: Mapped[str] = mapped_column(String(64), default="ingestion", nullable=False)
	human_gate_status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
	contact_number: Mapped[str | None] = mapped_column(String(64))
	product_id: Mapped[str | None] = mapped_column(String(64))
	state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
