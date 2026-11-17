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

from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert as pg_insert


# ============================================================
# 5. MODULE 2: COMPANY PROFILE, OHLCV & FINANCIALS CRUD
# ============================================================

def upsert_company_profile(db: Session, profile_data: Dict[str, Any]) -> models.Company:
    """
    Inserts or updates a company profile in PostgreSQL, recording data_source and retrieved_at.
    """
    now_utc = datetime.now(timezone.utc)
    stmt = pg_insert(models.Company).values(
        ticker_symbol=profile_data["ticker_symbol"].upper().strip(),
        company_name=profile_data["company_name"],
        exchange=profile_data["exchange"],
        currency=profile_data["currency"],
        sector=profile_data.get("sector"),
        industry=profile_data.get("industry"),
        description=profile_data.get("description"),
        website=profile_data.get("website"),
        market_cap=profile_data.get("market_cap"),
        extra_profile=profile_data.get("extra_profile", {}),
        data_source=profile_data["data_source"],
        retrieved_at=now_utc
    )

    update_cols = {
        "company_name": stmt.excluded.company_name,
        "exchange": stmt.excluded.exchange,
        "currency": stmt.excluded.currency,
        "sector": stmt.excluded.sector,
        "industry": stmt.excluded.industry,
        "description": stmt.excluded.description,
        "website": stmt.excluded.website,
        "market_cap": stmt.excluded.market_cap,
        "extra_profile": stmt.excluded.extra_profile,
        "data_source": stmt.excluded.data_source,
        "retrieved_at": now_utc,
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker_symbol"],
        set_=update_cols
    )
    db.execute(stmt)
    db.commit()

    return (
        db.query(models.Company)
        .filter(models.Company.ticker_symbol == profile_data["ticker_symbol"].upper().strip())
        .first()
    )


def search_companies_in_db(db: Session, query_str: str) -> List[models.Company]:
    """
    Searches cached companies in PostgreSQL by ticker symbol or company name.
    """
    q = f"%{query_str.strip()}%"
    return (
        db.query(models.Company)
        .filter(
            or_(
                models.Company.ticker_symbol.ilike(q),
                models.Company.company_name.ilike(q)
            )
        )
        .limit(10)
        .all()
    )


def bulk_upsert_stock_prices(
    db: Session,
    ticker_symbol: str,
    cleaned_df: pd.DataFrame,
    data_source: str
) -> int:
    """
    Bulk inserts/updates validated OHLCV rows into stock_prices.
    Keeps trade_date and retrieved_at strictly separate.
    """
    if cleaned_df is None or cleaned_df.empty:
        return 0

    now_utc = datetime.now(timezone.utc)
    ticker = ticker_symbol.upper().strip()

    records = []
    for row in cleaned_df.to_dict(orient="records"):
        records.append({
            "price_id": uuid.uuid4(),
            "ticker_symbol": ticker,
            "trade_date": row["trade_date"],
            "open_price": row["open_price"],
            "high_price": row["high_price"],
            "low_price": row["low_price"],
            "close_price": row["close_price"],
            "volume": int(row["volume"]),
            "data_source": data_source,
            "retrieved_at": now_utc
        })

    stmt = pg_insert(models.StockPrice).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_ticker_trade_date",
        set_={
            "open_price": stmt.excluded.open_price,
            "high_price": stmt.excluded.high_price,
            "low_price": stmt.excluded.low_price,
            "close_price": stmt.excluded.close_price,
            "volume": stmt.excluded.volume,
            "data_source": stmt.excluded.data_source,
            "retrieved_at": now_utc
        }
    )
    db.execute(stmt)
    db.commit()
    return len(records)


def get_historical_prices(
    db: Session,
    ticker_symbol: str,
    limit: int = 365
) -> List[models.StockPrice]:
    """
    Retrieves stored OHLCV records for a stock ordered newest to oldest.
    """
    return (
        db.query(models.StockPrice)
        .filter(models.StockPrice.ticker_symbol == ticker_symbol.upper().strip())
        .order_by(models.StockPrice.trade_date.desc())
        .limit(limit)
        .all()
    )


def upsert_financial_statements(
    db: Session,
    ticker_symbol: str,
    statement_type: str,
    currency: str,
    cleaned_periods: Dict[str, Dict[str, Any]],
    data_source: str
) -> int:
    """
    Stores cleaned Income Statement, Balance Sheet, or Cash Flow JSONB records by fiscal period.
    """
    if not cleaned_periods:
        return 0

    now_utc = datetime.now(timezone.utc)
    ticker = ticker_symbol.upper().strip()
    s_type = statement_type.upper().strip()

    count = 0
    for period_str, metrics_dict in cleaned_periods.items():
        period_date = date.fromisoformat(period_str)
        stmt = pg_insert(models.FinancialStatement).values(
            statement_id=uuid.uuid4(),
            ticker_symbol=ticker,
            statement_type=s_type,
            period_ending=period_date,
            currency=currency,
            statement_data=metrics_dict,
            data_source=data_source,
            retrieved_at=now_utc
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_company_statement_period",
            set_={
                "currency": stmt.excluded.currency,
                "statement_data": stmt.excluded.statement_data,
                "data_source": stmt.excluded.data_source,
                "retrieved_at": now_utc
            }
        )
        db.execute(stmt)
        count += 1

    db.commit()
    return count


def get_company_financial_statements(
    db: Session,
    ticker_symbol: str,
    statement_type: Optional[str] = None
) -> List[models.FinancialStatement]:
    """
    Retrieves stored financial statements for a company.
    """
    query = db.query(models.FinancialStatement).filter(
        models.FinancialStatement.ticker_symbol == ticker_symbol.upper().strip()
    )
    if statement_type:
        query = query.filter(models.FinancialStatement.statement_type == statement_type.upper().strip())
    return query.order_by(models.FinancialStatement.period_ending.desc()).all()