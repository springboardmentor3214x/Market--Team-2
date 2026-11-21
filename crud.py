import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import hashlib


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

# ============================================================
# 6. MODULE 3: RESEARCH TASKS, AGENT RESULTS, SOURCES, REPORTS
# ============================================================

def create_research_task(
    db: Session,
    user_id: uuid.UUID,
    ticker_symbol: str,
    market: str,
    requested_period: str
) -> models.ResearchTask:
    """
    Creates a new research task when a user triggers stock analysis.
    Initial status is always PENDING.
    """
    task = models.ResearchTask(
        user_id=user_id,
        ticker_symbol=ticker_symbol.upper().strip(),
        market=market.upper().strip(),
        requested_period=requested_period,
        status=models.TaskStatus.PENDING
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_research_task(
    db: Session,
    task_id: uuid.UUID
) -> Optional[models.ResearchTask]:
    """
    Fetches a single research task by its UUID.
    Used by API endpoints to check task status.
    """
    return (
        db.query(models.ResearchTask)
        .filter(models.ResearchTask.task_id == task_id)
        .first()
    )


def get_research_tasks_by_user(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 20
) -> List[models.ResearchTask]:
    """
    Retrieves all research tasks for a specific user (most recent first).
    Used to populate research history on the dashboard.
    """
    return (
        db.query(models.ResearchTask)
        .filter(models.ResearchTask.user_id == user_id)
        .order_by(models.ResearchTask.created_at.desc())
        .limit(limit)
        .all()
    )


def update_task_status(
    db: Session,
    task_id: uuid.UUID,
    status: models.TaskStatus,
    error_message: Optional[str] = None
) -> Optional[models.ResearchTask]:
    """
    Updates the status of a research task (PENDING → RUNNING → COMPLETED/FAILED).
    Automatically sets completed_at when the task reaches a terminal state.
    """
    task = get_research_task(db, task_id)
    if not task:
        return None

    task.status = status

    if error_message:
        task.error_message = error_message

    # Set completion timestamp for terminal states
    if status in (
        models.TaskStatus.COMPLETED,
        models.TaskStatus.FAILED,
        models.TaskStatus.PARTIAL
    ):
        task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)
    return task


def upsert_agent_result(
    db: Session,
    task_id: uuid.UUID,
    agent_name: models.AgentName,
    status: models.AgentStatus,
    output_json: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Inserts or updates an agent's result for a given task.
    Safe to call multiple times — retries won't create duplicate rows.
    Uniqueness is enforced by (task_id, agent_name).
    """
    now_utc = datetime.now(timezone.utc)

    stmt = pg_insert(models.AgentResult).values(
        result_id=uuid.uuid4(),
        task_id=task_id,
        agent_name=agent_name,
        status=status,
        output_json=output_json,
        error_message=error_message,
        created_at=now_utc,
        updated_at=now_utc
    )

    stmt = stmt.on_conflict_do_update(
        constraint="uq_agent_result_task_agent",
        set_={
            "status":        stmt.excluded.status,
            "output_json":   stmt.excluded.output_json,
            "error_message": stmt.excluded.error_message,
            "updated_at":    now_utc
        }
    )

    db.execute(stmt)
    db.commit()


def get_agent_result(
    db: Session,
    task_id: uuid.UUID,
    agent_name: models.AgentName
) -> Optional[models.AgentResult]:
    """
    Fetches the result of a specific agent for a given task.
    """
    return (
        db.query(models.AgentResult)
        .filter(
            models.AgentResult.task_id == task_id,
            models.AgentResult.agent_name == agent_name
        )
        .first()
    )


def get_all_agent_results_for_task(
    db: Session,
    task_id: uuid.UUID
) -> List[models.AgentResult]:
    """
    Fetches results from ALL agents for a given task.
    Used by the Supervisor Agent (Module 4) to aggregate findings.
    """
    return (
        db.query(models.AgentResult)
        .filter(models.AgentResult.task_id == task_id)
        .all()
    )


def bulk_save_source_documents(
    db: Session,
    task_id: uuid.UUID,
    sources: List[Dict[str, Any]]
) -> int:
    """
    Batch inserts news/announcement sources linked to a research task.
    Deduplicates within the batch using SHA-256 of the source URL.

    Each dict in sources must have:
        - source_type (str): e.g. "NEWS_ARTICLE"
        - source_url  (str): the original URL
        - title       (str, optional)
        - published_at (datetime, optional)
    """
    if not sources:
        return 0

    now_utc = datetime.now(timezone.utc)
    seen_hashes = set()
    docs_to_insert = []

    for s in sources:
        url_hash = hashlib.sha256(s["source_url"].encode("utf-8")).hexdigest()

        # Skip duplicates within this batch
        if url_hash in seen_hashes:
            continue
        seen_hashes.add(url_hash)

        docs_to_insert.append(
            models.SourceDocument(
                task_id=task_id,
                source_type=s["source_type"],
                title=s.get("title"),
                source_url=s["source_url"],
                published_at=s.get("published_at"),
                retrieved_at=now_utc,
                content_hash=url_hash
            )
        )

    if docs_to_insert:
        db.add_all(docs_to_insert)
        db.commit()

    return len(docs_to_insert)


def save_research_report(
    db: Session,
    task_id: uuid.UUID,
    report_content: Dict[str, Any],
    summary: str,
    limitations: str
) -> models.ResearchReport:
    """
    Saves the final consolidated research report for a task.
    report_content is the full structured JSONB report from all agents.
    Called at the end of Module 4's Supervisor Agent workflow.
    """
    report = models.ResearchReport(
        task_id=task_id,
        report_content=report_content,
        summary=summary,
        limitations=limitations
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_by_task(
    db: Session,
    task_id: uuid.UUID
) -> Optional[models.ResearchReport]:
    """
    Retrieves the final research report for a given task.
    Returns None if the report hasn't been generated yet.
    """
    return (
        db.query(models.ResearchReport)
        .filter(models.ResearchReport.task_id == task_id)
        .first()
    )