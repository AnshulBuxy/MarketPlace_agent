from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Admin(UUIDMixin, TimestampMixin, Base):
	"""Admin user profile."""

	__tablename__ = "admins"

	email: Mapped[str] = mapped_column(String(255), unique=True)
	name: Mapped[str | None] = mapped_column(String(120))
	role: Mapped[str | None] = mapped_column(String(64))
	is_active: Mapped[bool] = mapped_column(Boolean, default=True)
