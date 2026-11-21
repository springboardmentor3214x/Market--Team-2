-- Enable UUID extension (for older Postgres compatibility, though PG 18 has gen_random_uuid() built-in)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Phase 2 & 3: Core Users Table + User Preferences
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    preferences JSONB DEFAULT '{"preferred_market": "NSE", "analysis_period": "1Y"}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index on email for fast login lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Phase 4: Workspace Tables (Watchlists & Research History)

-- 1. Watchlists Table (Saved Stocks)
CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker_symbol VARCHAR(50) NOT NULL,
    company_name VARCHAR(255),
    exchange VARCHAR(50) DEFAULT 'NSE',
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- Prevent a user from saving the exact same stock ticker twice
    CONSTRAINT uq_user_watchlist_ticker UNIQUE (user_id, ticker_symbol)
);

-- Index on user_id for fast watchlist retrieval
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);


-- 2. Research History Table (User-Specific Past Research)
CREATE TABLE IF NOT EXISTS research_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker_symbol VARCHAR(50) NOT NULL,
    company_name VARCHAR(255),
    analysis_period VARCHAR(50),
    research_summary JSONB, -- Optional: stores AI report metadata or key findings later
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index on user_id for fast research history lookups
CREATE INDEX IF NOT EXISTS idx_research_history_user_id ON research_history(user_id);


-- ============================================================
-- MODULE 2: STOCK SEARCH & MARKET DATA COLLECTION TABLES
-- ============================================================

-- 1. Companies Table (Company Profiles & Market Metadata)
CREATE TABLE IF NOT EXISTS companies (
    ticker_symbol VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL,          -- NSE, BSE, NYSE, NASDAQ
    currency VARCHAR(10) NOT NULL,          -- INR, USD
    sector VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    website VARCHAR(255),
    market_cap BIGINT,
    extra_profile JSONB DEFAULT '{}'::jsonb,
    data_source VARCHAR(100) NOT NULL,      -- e.g., 'Yahoo Finance (yfinance)'
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_exchange ON companies(exchange);


-- 2. Stock Prices Table (Validated Historical OHLCV Data)
CREATE TABLE IF NOT EXISTS stock_prices (
    price_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_symbol VARCHAR(50) NOT NULL REFERENCES companies(ticker_symbol) ON DELETE CASCADE,
    trade_date DATE NOT NULL,               -- Original trading session date
    open_price NUMERIC(15, 4) NOT NULL,
    high_price NUMERIC(15, 4) NOT NULL,
    low_price NUMERIC(15, 4) NOT NULL,
    close_price NUMERIC(15, 4) NOT NULL,
    volume BIGINT NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Separate from trade_date!

    -- Prevent duplicate trading dates for the same stock
    CONSTRAINT uq_ticker_trade_date UNIQUE (ticker_symbol, trade_date),

    -- Enforce logical OHLCV consistency at the database level
    CONSTRAINT chk_ohlcv_logical_consistency CHECK (
        high_price >= low_price AND
        high_price >= open_price AND
        high_price >= close_price AND
        low_price <= open_price AND
        low_price <= close_price AND
        open_price > 0 AND
        low_price > 0 AND
        volume >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices(ticker_symbol, trade_date DESC);


-- 3. Financial Statements Table (Income Statement, Balance Sheet, Cash Flow)
CREATE TABLE IF NOT EXISTS financial_statements (
    statement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_symbol VARCHAR(50) NOT NULL REFERENCES companies(ticker_symbol) ON DELETE CASCADE,
    statement_type VARCHAR(50) NOT NULL,    -- 'INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW'
    period_ending DATE NOT NULL,
    currency VARCHAR(10) NOT NULL,
    statement_data JSONB NOT NULL,          -- Line items stored as structured JSONB
    data_source VARCHAR(100) NOT NULL,
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_company_statement_period UNIQUE (ticker_symbol, statement_type, period_ending)
);

CREATE INDEX IF NOT EXISTS idx_fin_statements_ticker_type ON financial_statements(ticker_symbol, statement_type);