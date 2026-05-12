from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin
from .enums import ListingPackageStatus


class ListingPackage(UUIDMixin, TimestampMixin, Base):
	"""Bundled listing drafts for admin review."""

	__tablename__ = "listing_packages"

	product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))
	status: Mapped[ListingPackageStatus] = mapped_column(
		Enum(ListingPackageStatus, native_enum=False),
		nullable=False,
	)
	routing_rationale: Mapped[dict | None] = mapped_column(JSON)
	pricing_summary: Mapped[dict | None] = mapped_column(JSON)

	product = relationship("Product")
	drafts = relationship("CatalogDraft", back_populates="listing_package")
