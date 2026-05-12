from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin
from .enums import CatalogDraftStatus


class CatalogDraft(UUIDMixin, TimestampMixin, Base):
	"""Marketplace-specific catalog draft."""

	__tablename__ = "catalog_drafts"

	listing_package_id: Mapped[UUID | None] = mapped_column(ForeignKey("listing_packages.id"))
	marketplace_id: Mapped[UUID | None] = mapped_column(ForeignKey("marketplaces.id"))
	status: Mapped[CatalogDraftStatus] = mapped_column(
		Enum(CatalogDraftStatus, native_enum=False),
		nullable=False,
	)
	draft: Mapped[dict | None] = mapped_column(JSON)
	validation_errors: Mapped[dict | None] = mapped_column(JSON)

	listing_package = relationship("ListingPackage", back_populates="drafts")
	marketplace = relationship("Marketplace")
