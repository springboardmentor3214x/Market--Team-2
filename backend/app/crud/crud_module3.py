# backend/app/crud/crud_module3.py

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.models.research_models import (
    ResearchTask, AgentResult, SourceDocument, ResearchReport,
    TaskStatus, AgentName, AgentStatus, SourceType
)


# ── Research Tasks ────────────────────────────────────────────────────────────

def create_research_task(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    market: str,
    requested_period: str = "1y"
) -> ResearchTask:
    """Creates a new research task. Initial status is always PENDING."""
    task = ResearchTask(
        user_id=user_id,
        ticker_symbol=ticker_symbol.upper().strip(),
        market=market.upper().strip(),
        requested_period=requested_period,
        status=TaskStatus.PENDING
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_research_task(db: Session, task_id: uuid.UUID) -> Optional[ResearchTask]:
    return db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()


def get_research_tasks_by_user(
    db: Session, user_id: uuid.UUID, limit: int = 20
) -> List[ResearchTask]:
    return (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == user_id)
        .order_by(ResearchTask.created_at.desc())
        .limit(limit)
        .all()
    )


def update_task_status(
    db: Session,
    task_id: uuid.UUID,
    status: TaskStatus,
    error_message: Optional[str] = None
) -> Optional[ResearchTask]:
    """Updates task status. Automatically sets completed_at for terminal states."""
    task = get_research_task(db, task_id)
    if not task:
        return None

    task.status = status
    if error_message:
        task.error_message = error_message
    if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PARTIAL):
        task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)
    return task


# ── Agent Results ─────────────────────────────────────────────────────────────

def upsert_agent_result(
    db: Session,
    task_id: uuid.UUID,
    agent_name: AgentName,
    status: AgentStatus,
    output_json: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Inserts or updates agent result for (task_id, agent_name).
    Safe for retries — will not create duplicate rows.
    """
    now_utc = datetime.now(timezone.utc)
    existing = get_agent_result(db, task_id, agent_name)

    if existing:
        existing.status        = status
        existing.output_json   = output_json
        existing.error_message = error_message
        existing.updated_at    = now_utc
    else:
        new_result = AgentResult(
            task_id=task_id,
            agent_name=agent_name,
            status=status,
            output_json=output_json,
            error_message=error_message,
            created_at=now_utc,
        )
        db.add(new_result)

    db.commit()


def get_agent_result(
    db: Session,
    task_id: uuid.UUID,
    agent_name: AgentName
) -> Optional[AgentResult]:
    return (
        db.query(AgentResult)
        .filter(
            AgentResult.task_id    == task_id,
            AgentResult.agent_name == agent_name
        )
        .first()
    )


def get_all_agent_results_for_task(
    db: Session, task_id: uuid.UUID
) -> List[AgentResult]:
    """Used by Supervisor Agent (Module 4) to aggregate all 4 agent outputs."""
    return db.query(AgentResult).filter(AgentResult.task_id == task_id).all()


# ── Source Documents ──────────────────────────────────────────────────────────

def bulk_save_source_documents(
    db: Session,
    task_id: uuid.UUID,
    sources: List[Dict[str, Any]]
) -> int:
    """
    Batch inserts news/announcement sources. Deduplicates by SHA-256 of URL.
    Each dict needs: source_type, source_url. Optional: title, published_at.
    """
    seen = set()
    docs = []
    for s in sources:
        url_hash = hashlib.sha256(s["source_url"].encode()).hexdigest()
        if url_hash in seen:
            continue
        seen.add(url_hash)
        docs.append(SourceDocument(
            task_id=task_id,
            source_type=s["source_type"],
            title=s.get("title"),
            source_url=s["source_url"],
            published_at=s.get("published_at"),
            content_hash=url_hash,
        ))
    if docs:
        db.add_all(docs)
        db.commit()
    return len(docs)


# ── Research Reports ──────────────────────────────────────────────────────────

def save_research_report(
    db: Session,
    task_id: uuid.UUID,
    report_content: Dict[str, Any],
    summary: str,
    limitations: str
) -> ResearchReport:
    """Saves the final consolidated report. Called at end of Supervisor workflow."""
    report = ResearchReport(
        task_id=task_id,
        report_content=report_content,
        summary=summary,
        limitations=limitations,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_by_task(db: Session, task_id: uuid.UUID) -> Optional[ResearchReport]:
    return db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()