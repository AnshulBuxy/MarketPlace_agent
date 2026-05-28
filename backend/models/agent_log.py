from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AgentLog(TimestampMixin, UUIDMixin, Base):
	"""Log of agent interactions during conversation."""

	__tablename__ = "agent_logs"

	conversation_phone: Mapped[str] = mapped_column(String(64), ForeignKey("conversation_sessions.phone_number"), nullable=False)
	agent_name: Mapped[str] = mapped_column(String(64), nullable=False)  # "ConversationAgent", "ExtractionAgent", etc.
	agent_action: Mapped[str] = mapped_column(String(64), nullable=False)  # "request_image", "extract_and_summarize", etc.
	agent_input: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # Context dict passed to agent
	agent_output: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # Agent response/decision
	model_name: Mapped[str] = mapped_column(String(64), default="gemini-2.0-flash", nullable=False)  # Which Gemini model was used
	tokens_used: Mapped[int] = mapped_column(default=0, nullable=False)  # Approximate tokens
	error: Mapped[str | None] = mapped_column(Text, nullable=True)  # Any error that occurred
