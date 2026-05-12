from __future__ import annotations

from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin
from .enums import ProductStatus


class Product(UUIDMixin, TimestampMixin, Base):
	"""Product record from ingestion."""

	__tablename__ = "products"

	artisan_id: Mapped[UUID | None] = mapped_column(ForeignKey("artisans.id"))
	source_message_id: Mapped[UUID | None] = mapped_column(ForeignKey("inbound_messages.id"))
	status: Mapped[ProductStatus] = mapped_column(
		Enum(ProductStatus, native_enum=False),
		nullable=False,
	)
	image_url: Mapped[str | None] = mapped_column(String(512))
	image_url_enhanced: Mapped[str | None] = mapped_column(String(512))
	audio_url: Mapped[str | None] = mapped_column(String(512))
	transcript: Mapped[str | None] = mapped_column(Text)
	attributes: Mapped[dict | None] = mapped_column(JSON)
	image_quality_ok: Mapped[bool] = mapped_column(default=True, nullable=False)
	user_provided_description: Mapped[str | None] = mapped_column(Text)
	extraction_confidence: Mapped[float] = mapped_column(default=0.0, nullable=False)

	artisan = relationship("Artisan", back_populates="products")
	source_message = relationship("InboundMessage")
