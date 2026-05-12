from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_event import AuditEvent


async def log_event(
    session: AsyncSession,
    agent: str,
    action: str,
    input_data: dict | None,
    output_data: dict | None,
    product_id: UUID | None,
) -> AuditEvent:
    """Persist an audit event."""
    event = AuditEvent(
        agent=agent,
        action=action,
        input_data=input_data or {},
        output_data=output_data or {},
        product_id=product_id,
    )
    session.add(event)
    await session.flush()
    return event
