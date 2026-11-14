import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.research_history import ResearchHistory

def log_research_activity(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    company_name: Optional[str] = None,
    analysis_period: str = "1Y",
    research_summary: Optional[Dict[str, Any]] = None
) -> ResearchHistory:
    """
    Logs a stock research task tied to the user's account.
    """
    entry = ResearchHistory(
        user_id=user_id,
        ticker_symbol=ticker_symbol.upper().strip(),
        company_name=company_name,
        analysis_period=analysis_period,
        research_summary=research_summary
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_user_research_history(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 50
) -> List[ResearchHistory]:
    """
    Retrieves isolated research history for the specified user (most recent first).
    """
    return (
        db.query(ResearchHistory)
        .filter(ResearchHistory.user_id == user_id)
        .order_by(ResearchHistory.searched_at.desc())
        .limit(limit)
        .all()
    )
