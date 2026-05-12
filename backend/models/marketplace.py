from __future__ import annotations

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Marketplace(UUIDMixin, TimestampMixin, Base):
	"""Marketplace configuration."""

	__tablename__ = "marketplaces"

	name: Mapped[str] = mapped_column(String(120), unique=True)
	config: Mapped[dict | None] = mapped_column(JSON)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True)
