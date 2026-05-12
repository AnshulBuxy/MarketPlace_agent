from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Artisan(UUIDMixin, TimestampMixin, Base):
	"""Artisan profile."""

	__tablename__ = "artisans"

	name: Mapped[str | None] = mapped_column(String(120))
	phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
	language: Mapped[str | None] = mapped_column(String(32))
	location: Mapped[str | None] = mapped_column(String(120))
	craft: Mapped[str | None] = mapped_column(String(120))

	products = relationship("Product", back_populates="artisan")
	messages = relationship("InboundMessage", back_populates="artisan")
