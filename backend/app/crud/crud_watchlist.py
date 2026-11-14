import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.models.watchlist import Watchlist

def add_to_watchlist(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    company_name: Optional[str] = None,
    exchange: str = "NSE"
) -> Optional[Watchlist]:
    """
    Saves a stock to the user's watchlist.
    Returns None if the stock already exists in the watchlist.
    """
    item = Watchlist(
        user_id=user_id,
        ticker_symbol=ticker_symbol.upper().strip(),
        company_name=company_name,
        exchange=exchange.upper().strip()
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        return None

def get_user_watchlist(db: Session, user_id: uuid.UUID) -> List[Watchlist]:
    """
    Retrieves all watchlist items for the given user, ordered newest first.
    """
    return (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user_id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )

def remove_from_watchlist(
    db: Session,
    user_id: uuid.UUID,
    item_id_or_ticker: str
) -> bool:
    """
    Removes a watchlist item either by its UUID or by ticker symbol.
    """
    query = db.query(Watchlist).filter(Watchlist.user_id == user_id)
    
    # Try parsing as UUID first
    try:
        val_uuid = uuid.UUID(item_id_or_ticker)
        item = query.filter(Watchlist.watchlist_id == val_uuid).first()
    except (ValueError, AttributeError):
        item = None
        
    if not item:
        # Fall back to matching by ticker symbol
        item = query.filter(Watchlist.ticker_symbol == item_id_or_ticker.upper().strip()).first()

    if not item:
        return False

    db.delete(item)
    db.commit()
    return True
