import uuid
from sqlalchemy import (
    Column, String, Text, DateTime, Date, BigInteger, Numeric,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base


# ============================================================
# MODULE 1 MODELS: USERS & WORKSPACE
# ============================================================

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(
        JSONB,
        nullable=False,
        default=lambda: {"preferred_market": "NSE", "analysis_period": "1Y"}
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    research_history = relationship("ResearchHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


class Watchlist(Base):
    __tablename__ = "watchlists"

    watchlist_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker_symbol = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=True)
    exchange = Column(String(50), default="NSE")
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="watchlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "ticker_symbol", name="uq_user_watchlist_ticker"),
    )

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, ticker={self.ticker_symbol})>"


class ResearchHistory(Base):
    __tablename__ = "research_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker_symbol = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=True)
    analysis_period = Column(String(50), nullable=True)
    research_summary = Column(JSONB, nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="research_history")

    def __repr__(self):
        return f"<ResearchHistory(user_id={self.user_id}, ticker={self.ticker_symbol})>"


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
    extra_profile = Column(JSONB, nullable=False, default=dict)

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

    price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    statement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker_symbol = Column(
        String(50),
        ForeignKey("companies.ticker_symbol", ondelete="CASCADE"),
        nullable=False
    )
    statement_type = Column(String(50), nullable=False)  # 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW'
    period_ending = Column(Date, nullable=False)
    currency = Column(String(10), nullable=False)
    statement_data = Column(JSONB, nullable=False)       # Cleaned JSON dictionary of financial metrics

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