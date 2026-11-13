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