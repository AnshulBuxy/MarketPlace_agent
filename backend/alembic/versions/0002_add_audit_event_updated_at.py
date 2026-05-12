"""add audit_events updated_at

Revision ID: 0002_add_audit_event_updated_at
Revises: 0001_initial
Create Date: 2026-05-07 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_add_audit_event_updated_at"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add updated_at to audit_events."""
    op.add_column(
        "audit_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove updated_at from audit_events."""
    op.drop_column("audit_events", "updated_at")