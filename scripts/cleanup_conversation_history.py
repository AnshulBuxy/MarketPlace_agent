from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete, func, inspect, or_, select, update

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.db import AsyncSessionLocal  # noqa: E402
from backend.models.agent_log import AgentLog  # noqa: E402
from backend.models.artisan import Artisan  # noqa: E402
from backend.models.conversation_session import ConversationSession  # noqa: E402
from backend.models.inbound_message import InboundMessage  # noqa: E402
from backend.models.product import Product  # noqa: E402


def build_phone_candidates(raw_number: str) -> list[str]:
    number = raw_number.strip()
    if not number:
        return []

    candidates = {number}

    if number.startswith("whatsapp:"):
        stripped = number.removeprefix("whatsapp:")
        candidates.add(stripped)
        if stripped.startswith("+"):
            candidates.add(f"whatsapp:{stripped}")
    else:
        if number.startswith("+"):
            candidates.add(f"whatsapp:{number}")
        elif number.isdigit() and len(number) == 10:
            candidates.add(f"+91{number}")
            candidates.add(f"whatsapp:+91{number}")

    return sorted(candidates)


async def _count_rows(session, candidates: list[str]) -> dict[str, int]:
    table_names = await session.run_sync(lambda sync_session: set(inspect(sync_session.get_bind()).get_table_names()))

    session_count = 0
    if "conversation_sessions" in table_names:
        session_count = await session.scalar(
            select(func.count()).select_from(ConversationSession).where(ConversationSession.phone_number.in_(candidates))
        )

    log_count = 0
    if "agent_logs" in table_names:
        log_count = await session.scalar(
            select(func.count()).select_from(AgentLog).where(AgentLog.conversation_phone.in_(candidates))
        )

    inbound_count = 0
    if "inbound_messages" in table_names:
        inbound_count = await session.scalar(
            select(func.count()).select_from(InboundMessage).where(InboundMessage.from_number.in_(candidates))
        )

    artisan_count = 0
    if "artisans" in table_names:
        artisan_count = await session.scalar(
            select(func.count()).select_from(Artisan).where(Artisan.phone.in_(candidates))
        )

    product_count = 0
    if "products" in table_names and "inbound_messages" in table_names and "artisans" in table_names:
        inbound_ids = select(InboundMessage.id).where(InboundMessage.from_number.in_(candidates))
        artisan_ids = select(Artisan.id).where(Artisan.phone.in_(candidates))
        product_filter = or_(
            Product.artisan_id.in_(artisan_ids),
            Product.source_message_id.in_(inbound_ids),
        )
        product_count = await session.scalar(select(func.count()).select_from(Product).where(product_filter))

    return {
        "conversation_sessions": int(session_count or 0),
        "agent_logs": int(log_count or 0),
        "inbound_messages": int(inbound_count or 0),
        "artisans": int(artisan_count or 0),
        "products": int(product_count or 0),
    }


async def cleanup_conversation_history(raw_number: str, apply_changes: bool) -> None:
    candidates = build_phone_candidates(raw_number)
    if not candidates:
        raise ValueError("Phone number is required")

    async with AsyncSessionLocal() as session:
        table_names = await session.run_sync(lambda sync_session: set(inspect(sync_session.get_bind()).get_table_names()))
        counts = await _count_rows(session, candidates)
        print(f"Phone candidates: {', '.join(candidates)}")
        print("Rows that match:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

        if not apply_changes:
            print("Dry run only. Re-run with --apply to delete rows.")
            return

        if "products" in table_names and "inbound_messages" in table_names:
            inbound_ids = select(InboundMessage.id).where(InboundMessage.from_number.in_(candidates))
            await session.execute(
                update(Product)
                .where(Product.source_message_id.in_(inbound_ids))
                .values(source_message_id=None)
            )
        if "agent_logs" in table_names:
            await session.execute(delete(AgentLog).where(AgentLog.conversation_phone.in_(candidates)))
        if "conversation_sessions" in table_names:
            await session.execute(delete(ConversationSession).where(ConversationSession.phone_number.in_(candidates)))
        if "inbound_messages" in table_names:
            await session.execute(delete(InboundMessage).where(InboundMessage.from_number.in_(candidates)))

        await session.commit()
        print("Conversation history deleted successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete WhatsApp conversation history for a specific phone number."
    )
    parser.add_argument(
        "phone_number",
        nargs="?",
        default="7869291927",
        help="Phone number to delete, for example 7869291927 or whatsapp:+917869291927",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete rows. Without this flag the script only shows a dry run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(cleanup_conversation_history(args.phone_number, args.apply))


if __name__ == "__main__":
    main()