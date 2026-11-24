# backend/app/models/research_models.py

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime,
    Enum as SAEnum, UniqueConstraint, Index
)
from backend.app.db.session import Base, GUID, JSONType
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class TaskStatus(str, enum.Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    PARTIAL   = "PARTIAL"


class AgentName(str, enum.Enum):
    FUNDAMENTAL = "fundamental"
    TECHNICAL   = "technical"
    NEWS        = "news"
    RISK        = "risk"


class AgentStatus(str, enum.Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    SKIPPED   = "SKIPPED"


class SourceType(str, enum.Enum):
    NEWS_ARTICLE   = "NEWS_ARTICLE"
    COMPANY_FILING = "COMPANY_FILING"
    PRESS_RELEASE  = "PRESS_RELEASE"


# ── Models ────────────────────────────────────────────────────────────────────

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id          = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id          = Column(GUID(), nullable=False)
    ticker_symbol    = Column(String(20), nullable=False)
    market           = Column(String(20), nullable=False)
    requested_period = Column(String(20), nullable=False, default="1y")
    status           = Column(SAEnum(TaskStatus, name="taskstatus"), nullable=False, default=TaskStatus.PENDING)
    error_message    = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at     = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_research_tasks_user_id", "user_id"),
        Index("ix_research_tasks_ticker",  "ticker_symbol"),
        Index("ix_research_tasks_status",  "status"),
    )


class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id     = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id       = Column(GUID(), nullable=False)
    agent_name    = Column(SAEnum(AgentName, name="agentname"), nullable=False)
    status        = Column(SAEnum(AgentStatus, name="agentstatus"), nullable=False, default=AgentStatus.PENDING)
    output_json   = Column(JSONType(), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("task_id", "agent_name", name="uq_agent_result_task_agent"),
        Index("ix_agent_results_task_id", "task_id"),
    )


class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id    = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id      = Column(GUID(), nullable=False)
    source_type  = Column(SAEnum(SourceType, name="sourcetype"), nullable=False)
    title        = Column(Text, nullable=True)
    source_url   = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    content_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_source_documents_task_id",      "task_id"),
        Index("ix_source_documents_content_hash", "content_hash"),
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id      = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id        = Column(GUID(), nullable=False, unique=True)
    report_content = Column(JSONType(), nullable=True)
    summary        = Column(Text, nullable=True)
    limitations    = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_research_reports_task_id", "task_id"),
    )