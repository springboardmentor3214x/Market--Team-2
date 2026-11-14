from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.research_history import ResearchCreate, ResearchItem
from backend.app.crud.crud_research import (
    log_research_activity,
    get_user_research_history
)

router = APIRouter(prefix="/research-history", tags=["Research History"])

@router.get("", response_model=List[ResearchItem])
def list_research_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user-isolated research history for the currently logged-in user.
    """
    entries = get_user_research_history(db, current_user.user_id, limit=limit)
    return [
        {
            "id": str(e.history_id),
            "history_id": str(e.history_id),
            "stock_symbol": e.ticker_symbol,
            "ticker_symbol": e.ticker_symbol,
            "company_name": e.company_name or e.ticker_symbol,
            "analysis_period": e.analysis_period or "1Y",
            "research_summary": e.research_summary,
            "created_at": e.searched_at.strftime("%Y-%m-%d %H:%M:%S") if e.searched_at else "",
            "searched_at": e.searched_at.isoformat() if e.searched_at else ""
        }
        for e in entries
    ]

@router.post("", response_model=ResearchItem, status_code=status.HTTP_201_CREATED)
def record_research(
    item_in: ResearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logs a new stock research activity associated with the user's ID.
    """
    symbol = item_in.stock_symbol or item_in.ticker_symbol
    if not symbol or not symbol.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol is required"
        )

    ticker = symbol.upper().strip()
    company = item_in.company_name or ticker
    period = item_in.analysis_period or "1Y"

    entry = log_research_activity(
        db=db,
        user_id=current_user.user_id,
        ticker_symbol=ticker,
        company_name=company,
        analysis_period=period,
        research_summary=item_in.research_summary
    )

    return {
        "id": str(entry.history_id),
        "history_id": str(entry.history_id),
        "stock_symbol": entry.ticker_symbol,
        "ticker_symbol": entry.ticker_symbol,
        "company_name": entry.company_name,
        "analysis_period": entry.analysis_period,
        "research_summary": entry.research_summary,
        "created_at": entry.searched_at.strftime("%Y-%m-%d %H:%M:%S") if entry.searched_at else "",
        "searched_at": entry.searched_at.isoformat() if entry.searched_at else ""
    }
