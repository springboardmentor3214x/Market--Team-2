"""
data_access.py — Clean data-fetching layer for all agents.

Agents must call these functions instead of writing raw SQLAlchemy queries.
Returns plain Python types (DataFrames, dicts) — no SQLAlchemy objects leak out.
"""

from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session

import crud
import models


# ============================================================
# 1. STOCK PRICE SERIES  (used by: Technical Agent, Risk Agent)
# ============================================================

def get_price_dataframe(
    db: Session,
    ticker_symbol: str,
    limit: int = 365
) -> pd.DataFrame:
    """
    Returns OHLCV data as a clean DataFrame sorted oldest → newest.

    Columns: trade_date, open, high, low, close, volume

    Minimum rows needed by indicators:
        RSI   → 14 rows
        MACD  → 26 rows
        SMA50 → 50 rows
    Returns empty DataFrame if no data exists — agents must handle this.
    """
    rows = crud.get_historical_prices(db, ticker_symbol, limit=limit)

    if not rows:
        return pd.DataFrame(
            columns=["trade_date", "open", "high", "low", "close", "volume"]
        )

    df = pd.DataFrame([
        {
            "trade_date": row.trade_date,
            "open":       float(row.open_price),
            "high":       float(row.high_price),
            "low":        float(row.low_price),
            "close":      float(row.close_price),
            "volume":     int(row.volume)
        }
        for row in rows
    ])

    # crud returns newest-first; agents need oldest-first for indicator math
    df = df.sort_values("trade_date", ascending=True).reset_index(drop=True)
    return df


def get_latest_close_price(
    db: Session,
    ticker_symbol: str
) -> Optional[float]:
    """
    Returns the single most recent closing price for a ticker.
    Used by Fundamental Agent to calculate P/E and P/B ratios.
    Returns None if no price data exists.
    """
    rows = crud.get_historical_prices(db, ticker_symbol, limit=1)
    if not rows:
        return None
    return float(rows[0].close_price)


# ============================================================
# 2. COMPANY PROFILE  (used by: Fundamental Agent, Risk Agent)
# ============================================================

def get_company_info(
    db: Session,
    ticker_symbol: str
) -> Optional[dict]:
    """
    Returns company profile as a plain dict.
    Returns None if company not found in DB.
    """
    company = (
        db.query(models.Company)
        .filter(models.Company.ticker_symbol == ticker_symbol.upper().strip())
        .first()
    )

    if not company:
        return None

    return {
        "ticker_symbol": company.ticker_symbol,
        "company_name":  company.company_name,
        "exchange":      company.exchange,
        "currency":      company.currency,
        "sector":        company.sector,
        "industry":      company.industry,
        "description":   company.description,
        "website":       company.website,
        "market_cap":    float(company.market_cap) if company.market_cap else None,
        "retrieved_at":  company.retrieved_at.isoformat() if company.retrieved_at else None
    }


# ============================================================
# 3. FINANCIAL STATEMENTS  (used by: Fundamental Agent)
# ============================================================

def get_income_statements(
    db: Session,
    ticker_symbol: str,
    limit: int = 4
) -> list[dict]:
    """
    Returns the most recent Income Statements as a list of dicts.
    Each dict contains: fiscal_period (str) + all metrics from JSONB.

    Returns empty list if none found.
    limit=4 gives 4 years of annual data for YoY growth calculations.
    """
    rows = crud.get_company_financial_statements(
        db, ticker_symbol, statement_type="INCOME_STATEMENT"
    )
    return _statements_to_dicts(rows[:limit])


def get_balance_sheets(
    db: Session,
    ticker_symbol: str,
    limit: int = 4
) -> list[dict]:
    """
    Returns the most recent Balance Sheets as a list of dicts.
    """
    rows = crud.get_company_financial_statements(
        db, ticker_symbol, statement_type="BALANCE_SHEET"
    )
    return _statements_to_dicts(rows[:limit])


def get_cash_flow_statements(
    db: Session,
    ticker_symbol: str,
    limit: int = 4
) -> list[dict]:
    """
    Returns the most recent Cash Flow Statements as a list of dicts.
    """
    rows = crud.get_company_financial_statements(
        db, ticker_symbol, statement_type="CASH_FLOW"
    )
    return _statements_to_dicts(rows[:limit])


def _statements_to_dicts(rows: list) -> list[dict]:
    """
    Internal helper: converts FinancialStatement model rows → plain dicts.
    Merges the JSONB statement_data with the period metadata.
    """
    result = []
    for row in rows:
        entry = {"fiscal_period": row.period_ending.isoformat()}
        # Merge JSONB fields directly into the dict
        if row.statement_data:
            entry.update(row.statement_data)
        result.append(entry)
    return result


# ============================================================
# 4. DATA AVAILABILITY CHECK  (used by all agents on startup)
# ============================================================

def check_data_availability(
    db: Session,
    ticker_symbol: str
) -> dict:
    """
    Returns a summary of what data is available for a ticker.
    Agents call this first to decide what analysis is possible
    and what limitations to report.

    Example return:
    {
        "ticker": "INFY",
        "has_company_profile": True,
        "price_rows": 252,
        "has_enough_for_rsi": True,
        "has_enough_for_macd": True,
        "has_enough_for_sma50": True,
        "income_statement_periods": 4,
        "balance_sheet_periods": 4,
        "cash_flow_periods": 3
    }
    """
    ticker = ticker_symbol.upper().strip()

    price_rows = crud.get_historical_prices(db, ticker, limit=365)
    price_count = len(price_rows)

    income    = crud.get_company_financial_statements(db, ticker, "INCOME_STATEMENT")
    balance   = crud.get_company_financial_statements(db, ticker, "BALANCE_SHEET")
    cashflow  = crud.get_company_financial_statements(db, ticker, "CASH_FLOW")

    company = (
        db.query(models.Company)
        .filter(models.Company.ticker_symbol == ticker)
        .first()
    )

    return {
        "ticker":                     ticker,
        "has_company_profile":        company is not None,
        "price_rows":                 price_count,
        "has_enough_for_rsi":         price_count >= 14,
        "has_enough_for_macd":        price_count >= 26,
        "has_enough_for_sma50":       price_count >= 50,
        "income_statement_periods":   len(income),
        "balance_sheet_periods":      len(balance),
        "cash_flow_periods":          len(cashflow),
    }