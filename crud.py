import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models


# ==========================================
# 1. USER AUTHENTICATION & REGISTRATION CRUD
# ==========================================

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Used during Login and Registration to check if an email exists.
    """
    return db.query(models.User).filter(models.User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """
    Used by JWT protected routes to fetch the currently logged-in user.
    """
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password_hash: str,
    preferences: Optional[Dict[str, Any]] = None
) -> models.User:
    """
    Inserts a new user into PostgreSQL with a pre-hashed password.
    """
    default_prefs = preferences or {"preferred_market": "NSE", "analysis_period": "1Y"}
    new_user = models.User(
        email=email.lower().strip(),
        password_hash=password_hash,
        preferences=default_prefs
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ==========================================
# 2. USER PREFERENCES CRUD
# ==========================================

def update_user_preferences(
    db: Session,
    user_id: uuid.UUID,
    new_preferences: Dict[str, Any]
) -> Optional[models.User]:
    """
    Updates a user's preferred stock market (NSE/BSE, NYSE) and analysis period.
    Merges existing preferences with new keys.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    updated_prefs = dict(user.preferences or {})
    updated_prefs.update(new_preferences)
    
    user.preferences = updated_prefs
    db.commit()
    db.refresh(user)
    return user


# ==========================================
# 3. WATCHLIST (SAVED STOCKS) CRUD
# ==========================================

def add_to_watchlist(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    company_name: Optional[str] = None,
    exchange: str = "NSE"
) -> Optional[models.Watchlist]:
    """
    Saves a stock to a specific user's watchlist.
    Returns None if the stock is already in their watchlist.
    """
    item = models.Watchlist(
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
        # Triggered if (user_id, ticker_symbol) unique constraint is violated
        db.rollback()
        return None


def get_user_watchlist(db: Session, user_id: uuid.UUID) -> List[models.Watchlist]:
    """
    Fetches ONLY the logged-in user's saved stocks (newest first).
    """
    return (
        db.query(models.Watchlist)
        .filter(models.Watchlist.user_id == user_id)
        .order_by(models.Watchlist.added_at.desc())
        .all()
    )


def remove_from_watchlist(db: Session, user_id: uuid.UUID, ticker_symbol: str) -> bool:
    """
    Removes a stock from a user's watchlist.
    """
    item = (
        db.query(models.Watchlist)
        .filter(
            models.Watchlist.user_id == user_id,
            models.Watchlist.ticker_symbol == ticker_symbol.upper().strip()
        )
        .first()
    )
    if not item:
        return False

    db.delete(item)
    db.commit()
    return True


# ==========================================
# 4. USER-SPECIFIC RESEARCH HISTORY CRUD
# ==========================================

def log_research_activity(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    company_name: Optional[str] = None,
    analysis_period: str = "1Y",
    research_summary: Optional[Dict[str, Any]] = None
) -> models.ResearchHistory:
    """
    Records a stock research task associated with a specific user's ID.
    """
    entry = models.ResearchHistory(
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
    limit: int = 20
) -> List[models.ResearchHistory]:
    """
    Retrieves isolated research history for a specific user (most recent first).
    """
    return (
        db.query(models.ResearchHistory)
        .filter(models.ResearchHistory.user_id == user_id)
        .order_by(models.ResearchHistory.searched_at.desc())
        .limit(limit)
        .all()
    )