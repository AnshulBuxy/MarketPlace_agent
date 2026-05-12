"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-07 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artisans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120)),
        sa.Column("phone", sa.String(length=32), nullable=False, unique=True),
        sa.Column("language", sa.String(length=32)),
        sa.Column("location", sa.String(length=120)),
        sa.Column("craft", sa.String(length=120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inbound_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_sid", sa.String(length=64)),
        sa.Column("from_number", sa.String(length=32), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("num_media", sa.Integer(), server_default="0"),
        sa.Column("media_urls", sa.JSON()),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("artisan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artisans.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("artisan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artisans.id")),
        sa.Column(
            "source_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inbound_messages.id"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("image_url", sa.String(length=512)),
        sa.Column("audio_url", sa.String(length=512)),
        sa.Column("transcript", sa.Text()),
        sa.Column("attributes", sa.JSON()),
        sa.Column("image_quality_ok", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "marketplaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("config", sa.JSON()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "listing_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("routing_rationale", sa.JSON()),
        sa.Column("pricing_summary", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "catalog_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "listing_package_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listing_packages.id"),
        ),
        sa.Column("marketplace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplaces.id")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("draft", sa.JSON()),
        sa.Column("validation_errors", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120)),
        sa.Column("role", sa.String(length=64)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("input_data", sa.JSON()),
        sa.Column("output_data", sa.JSON()),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("admins")
    op.drop_table("catalog_drafts")
    op.drop_table("listing_packages")
    op.drop_table("marketplaces")
    op.drop_table("products")
    op.drop_table("inbound_messages")
    op.drop_table("artisans")

