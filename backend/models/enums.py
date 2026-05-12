from __future__ import annotations

from enum import Enum


class MessageType(str, Enum):
    """Inbound message type."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


class ProductStatus(str, Enum):
    """Product processing status."""

    INGESTED = "ingested"
    EXTRACTED = "extracted"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ListingPackageStatus(str, Enum):
    """Listing package status."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class CatalogDraftStatus(str, Enum):
    """Catalog draft status."""

    DRAFT = "draft"
    LIVE = "live"
    REJECTED = "rejected"
