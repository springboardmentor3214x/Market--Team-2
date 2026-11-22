import uuid
import enum
from sqlalchemy import (
    Column, String, Text, DateTime, Date, BigInteger, Numeric,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, func,
    Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base, GUID, JSONType

# Re-export Module 1 models
from backend.app.models.user import User
from backend.app.models.watchlist import Watchlist
from backend.app.models.research_history import ResearchHistory


# ============================================================
# MODULE 2 MODELS: COMPANY PROFILES, OHLCV & FINANCIALS
# ============================================================

class Company(Base):
    __tablename__ = "companies"

    ticker_symbol = Column(String(50), primary_key=True)  # e.g., 'INFY.NS', 'RELIANCE.NS', 'AAPL'
    company_name = Column(String(255), nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)  # 'NSE', 'BSE', 'NYSE', 'NASDAQ'
    currency = Column(String(10), nullable=False)              # 'INR', 'USD'
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    extra_profile = Column(JSONType, nullable=False, default=dict)

    # Audit tracking
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    stock_prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")
    financial_statements = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(ticker={self.ticker_symbol}, name={self.company_name}, exchange={self.exchange})>"


class StockPrice(Base):
    __tablename__ = "stock_prices"

    price_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ticker_symbol = Column(
        String(50),
        ForeignKey("companies.ticker_symbol", ondelete="CASCADE"),
        nullable=False
    )
    trade_date = Column(Date, nullable=False)  # Original trading session date

    # OHLCV Values
    open_price = Column(Numeric(15, 4), nullable=False)
    high_price = Column(Numeric(15, 4), nullable=False)
    low_price = Column(Numeric(15, 4), nullable=False)
    close_price = Column(Numeric(15, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)

    # Audit tracking (strictly separate from trade_date)
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company = relationship("Company", back_populates="stock_prices")

    __table_args__ = (
        UniqueConstraint("ticker_symbol", "trade_date", name="uq_ticker_trade_date"),
        CheckConstraint(
            "high_price >= low_price AND "
            "high_price >= open_price AND "
            "high_price >= close_price AND "
            "low_price <= open_price AND "
            "low_price <= close_price AND "
            "open_price > 0 AND low_price > 0 AND volume >= 0",
            name="chk_ohlcv_logical_consistency"
        ),
        Index("idx_stock_prices_ticker_date", "ticker_symbol", "trade_date"),
    )

    def __repr__(self):
        return f"<StockPrice(ticker={self.ticker_symbol}, date={self.trade_date}, close={self.close_price})>"


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    statement_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ticker_symbol = Column(
        String(50),
        ForeignKey("companies.ticker_symbol", ondelete="CASCADE"),
        nullable=False
    )
    statement_type = Column(String(50), nullable=False)  # 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW'
    period_ending = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False)
    statement_data = Column(JSONType, nullable=False)       # Cleaned JSON dictionary of financial metrics

    # Audit tracking
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company = relationship("Company", back_populates="financial_statements")

    __table_args__ = (
        UniqueConstraint("ticker_symbol", "statement_type", "period_ending", name="uq_company_statement_period"),
        Index("idx_fin_statements_ticker_type", "ticker_symbol", "statement_type"),
    )

    def __repr__(self):
        return f"<FinancialStatement(ticker={self.ticker_symbol}, type={self.statement_type}, period={self.period_ending})>"


# ============================================================
# MODULE 3 MODELS: TASKS, AGENT RESULTS, SOURCES & REPORTS
# ============================================================

# ── Enums ────────────────────────────────────────────────────────────────────

class TaskStatus(str, enum.Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    PARTIAL   = "PARTIAL"   # some agents succeeded, some failed


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
    NEWS_ARTICLE    = "NEWS_ARTICLE"
    COMPANY_FILING  = "COMPANY_FILING"
    PRESS_RELEASE   = "PRESS_RELEASE"
    ANALYST_REPORT  = "ANALYST_REPORT"


# ── Models ───────────────────────────────────────────────────────────────────

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id          = Column(GUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker_symbol    = Column(String(20), nullable=False)
    market           = Column(String(20), nullable=False)        # NSE, BSE, NYSE, NASDAQ
    requested_period = Column(String(20), nullable=False)        # e.g. "1y", "6mo", "3mo"
    status           = Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    error_message    = Column(Text, nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at     = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_research_tasks_user_id", "user_id"),
        Index("ix_research_tasks_ticker",  "ticker_symbol"),
        Index("ix_research_tasks_status",  "status"),
    )


class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id     = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id       = Column(GUID, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False)
    agent_name    = Column(SAEnum(AgentName), nullable=False)
    status        = Column(SAEnum(AgentStatus), nullable=False, default=AgentStatus.PENDING)
    output_json   = Column(JSONType, nullable=True)   # full Pydantic model serialized here
    error_message = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("task_id", "agent_name", name="uq_agent_result_task_agent"),
        Index("ix_agent_results_task_id", "task_id"),
    )


class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id    = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id      = Column(GUID, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False)
    source_type  = Column(SAEnum(SourceType), nullable=False)
    title        = Column(Text, nullable=True)
    source_url   = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content_hash = Column(String(64), nullable=True)   # SHA-256 hex for deduplication

    __table_args__ = (
        Index("ix_source_documents_task_id",      "task_id"),
        Index("ix_source_documents_content_hash", "content_hash"),
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id      = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id        = Column(GUID, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, unique=True)
    report_content = Column(JSONType, nullable=True)   # full structured report
    summary        = Column(Text, nullable=True)    # short plain-text summary
    limitations    = Column(Text, nullable=True)    # data gaps, disclaimers
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_research_reports_task_id", "task_id"),
    )


# Compatibility aliases
StockMetadata = Company
HistoricalPrice = StockPrice

__all__ = [
    "Base",
    "User",
    "Watchlist",
    "ResearchHistory",
    "Company",
    "StockPrice",
    "FinancialStatement",
    "StockMetadata",
    "HistoricalPrice",
    "TaskStatus",
    "AgentName",
    "AgentStatus",
    "SourceType",
    "ResearchTask",
    "AgentResult",
    "SourceDocument",
    "ResearchReport",
]
