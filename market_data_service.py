from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import requests
import yfinance as yf
from sqlalchemy.orm import Session

import crud
from data_validator import validate_ohlcv_dataframe, clean_financial_statement_df

DATA_SOURCE_NAME = "Yahoo Finance API (yfinance)"

# Supported Exchanges Map (maps Yahoo exchange codes to standard names & currencies)
SUPPORTED_EXCHANGES = {
    "NSI": ("NSE", "INR"),
    "NSE": ("NSE", "INR"),
    "BOM": ("BSE", "INR"),
    "BSE": ("BSE", "INR"),
    "NYQ": ("NYSE", "USD"),
    "NYSE": ("NYSE", "USD"),
    "NMS": ("NASDAQ", "USD"),
    "NGM": ("NASDAQ", "USD"),
    "NCM": ("NASDAQ", "USD"),
    "NASDAQ": ("NASDAQ", "USD"),
}

# Built-in fast lookup map for common company names/tickers across India & US
KNOWN_COMPANIES_MAP = {
    "INFOSYS": "INFY.NS",
    "INFY": "INFY.NS",
    "RELIANCE": "RELIANCE.NS",
    "RELIANCE INDUSTRIES": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "TATA CONSULTANCY SERVICES": "TCS.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "APPLE": "AAPL",
    "AAPL": "AAPL",
    "MICROSOFT": "MSFT",
    "MSFT": "MSFT",
}


def normalize_exchange_and_currency(ticker: str, raw_exchange: str, raw_currency: str) -> tuple[str, str]:
    """
    Ensures accurate exchange (NSE, BSE, NYSE, NASDAQ) and currency (INR, USD) metadata.
    """
    ticker_upper = ticker.upper()
    if ticker_upper.endswith(".NS"):
        return "NSE", "INR"
    if ticker_upper.endswith(".BO"):
        return "BSE", "INR"

    raw_ex_upper = (raw_exchange or "").upper()
    if raw_ex_upper in SUPPORTED_EXCHANGES:
        ex, default_curr = SUPPORTED_EXCHANGES[raw_ex_upper]
        return ex, (raw_currency or default_curr).upper()

    return (raw_exchange or "NYSE").upper(), (raw_currency or "USD").upper()


def search_company(query: str, preferred_market: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Requirement 1 & 7: Search companies by Company Name or Ticker Symbol across
    NSE, BSE, NYSE, and Nasdaq. Handles invalid queries cleanly.
    """
    if not query or not query.strip():
        return []

    clean_q = query.strip()
    results: List[Dict[str, Any]] = []

    # 1. Query Yahoo Finance's autocomplete search endpoint
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"q": clean_q, "quotesCount": 10, "newsCount": 0}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=8)
        if resp.status_code == 200:
            quotes = resp.json().get("quotes", [])
            for q in quotes:
                if q.get("quoteType") != "EQUITY":
                    continue
                symbol = q.get("symbol", "")
                raw_ex = q.get("exchange", "")
                # Filter to supported markets (NSE, BSE, NYSE, NASDAQ)
                if raw_ex in SUPPORTED_EXCHANGES or symbol.endswith((".NS", ".BO")):
                    exchange_name, currency = normalize_exchange_and_currency(symbol, raw_ex, None)
                    results.append({
                        "ticker_symbol": symbol,
                        "company_name": q.get("longname") or q.get("shortname") or symbol,
                        "exchange": exchange_name,
                        "currency": currency,
                        "sector": q.get("sector"),
                        "industry": q.get("industry"),
                        "data_source": DATA_SOURCE_NAME
                    })
    except Exception:
        pass

    # 2. Fallback to known company lookup if Yahoo search endpoint returned nothing
    if not results and clean_q.upper() in KNOWN_COMPANIES_MAP:
        mapped_ticker = KNOWN_COMPANIES_MAP[clean_q.upper()]
        ex, curr = normalize_exchange_and_currency(mapped_ticker, "", "")
        results.append({
            "ticker_symbol": mapped_ticker,
            "company_name": clean_q.title(),
            "exchange": ex,
            "currency": curr,
            "sector": None,
            "industry": None,
            "data_source": DATA_SOURCE_NAME
        })

    # Prioritize user's preferred_market (e.g., 'NSE' or 'BSE') if specified
    if preferred_market and results:
        pref = preferred_market.upper()
        results.sort(key=lambda x: 0 if pref in x["exchange"].upper() else 1)

    return results


def collect_and_store_stock_data(
    db: Session,
    query_or_ticker: str,
    period: str = "1y",
    preferred_market: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete Module 2 Pipeline:
      1. Resolves company name or ticker symbol (NSE, BSE, NYSE, NASDAQ).
      2. Fetches & stores Company Profile with source and timestamp.
      3. Fetches, validates (Pandas/NumPy), and stores Historical OHLCV prices.
      4. Fetches, cleans, and stores Income Statement, Balance Sheet, and Cash Flow.
    """
    retrieved_timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Resolve Ticker Symbol if user entered a company name like "Infosys" or "Reliance"
    clean_input = query_or_ticker.strip()
    upper_input = clean_input.upper()

    if upper_input in KNOWN_COMPANIES_MAP and not upper_input.endswith((".NS", ".BO")):
        resolved_ticker = KNOWN_COMPANIES_MAP[upper_input]
        if preferred_market and preferred_market.upper() == "BSE" and resolved_ticker.endswith(".NS"):
            resolved_ticker = resolved_ticker.replace(".NS", ".BO")
    elif " " in clean_input or len(clean_input) > 6 and not clean_input.upper().endswith((".NS", ".BO")):
        matches = search_company(clean_input, preferred_market=preferred_market)
        if not matches:
            return {
                "status": "error",
                "message": f"No publicly traded company found matching '{query_or_ticker}' in NSE, BSE, NYSE, or NASDAQ."
            }
        resolved_ticker = matches[0]["ticker_symbol"]
    else:
        resolved_ticker = upper_input
        # If user typed "TCS" or "INFY" with preferred_market="NSE", try resolving properly
        matches = search_company(resolved_ticker, preferred_market=preferred_market)
        if matches:
            resolved_ticker = matches[0]["ticker_symbol"]

    # Step 2: Connect to yfinance for the resolved ticker
    yf_ticker = yf.Ticker(resolved_ticker)

    # Fetch historical OHLCV first (reliable check for whether ticker actually exists)
    yf_period = period.lower().strip() if period else "1y"
    if yf_period not in ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"]:
        yf_period = "1y"

    try:
        raw_hist_df = yf_ticker.history(period=yf_period, interval="1d", auto_adjust=False)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve market data for '{resolved_ticker}': {str(e)}"
        }

    if raw_hist_df is None or raw_hist_df.empty:
        return {
            "status": "error",
            "message": f"Invalid ticker symbol or no historical market data available for '{query_or_ticker}' (resolved as '{resolved_ticker}')."
        }

    # Step 3: Retrieve & Store Company Profile
    info: Dict[str, Any] = {}
    try:
        info = yf_ticker.info or {}
    except Exception:
        info = {}

    exchange, currency = normalize_exchange_and_currency(
        resolved_ticker,
        info.get("exchange", ""),
        info.get("currency", "")
    )

    profile_payload = {
        "ticker_symbol": resolved_ticker,
        "company_name": info.get("longName") or info.get("shortName") or resolved_ticker,
        "exchange": exchange,
        "currency": currency,
        "sector": info.get("sector") or "Not Available",
        "industry": info.get("industry") or "Not Available",
        "description": info.get("longBusinessSummary") or "Company description not available from provider.",
        "website": info.get("website"),
        "market_cap": info.get("marketCap"),
        "extra_profile": {
            "country": info.get("country"),
            "full_time_employees": info.get("fullTimeEmployees"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        },
        "data_source": DATA_SOURCE_NAME
    }

    company_record = crud.upsert_company_profile(db, profile_payload)

    # Step 4: Validate & Store Historical OHLCV Data
    cleaned_ohlcv_df, validation_report = validate_ohlcv_dataframe(raw_hist_df)
    prices_stored_count = crud.bulk_upsert_stock_prices(
        db=db,
        ticker_symbol=resolved_ticker,
        cleaned_df=cleaned_ohlcv_df,
        data_source=DATA_SOURCE_NAME
    )

    # Step 5: Retrieve, Clean & Store Financial Statements (Income Statement, Balance Sheet, Cash Flow)
    statements_summary: Dict[str, Any] = {}
    statement_fetch_map = {
        "INCOME_STATEMENT": lambda: yf_ticker.income_stmt,
        "BALANCE_SHEET": lambda: yf_ticker.balance_sheet,
        "CASH_FLOW": lambda: yf_ticker.cashflow,
    }

    for stmt_type, fetcher in statement_fetch_map.items():
        try:
            raw_stmt_df = fetcher()
            cleaned_periods = clean_financial_statement_df(raw_stmt_df)
            if cleaned_periods:
                periods_saved = crud.upsert_financial_statements(
                    db=db,
                    ticker_symbol=resolved_ticker,
                    statement_type=stmt_type,
                    currency=currency,
                    cleaned_periods=cleaned_periods,
                    data_source=DATA_SOURCE_NAME
                )
                statements_summary[stmt_type] = {
                    "available": True,
                    "periods_stored": periods_saved,
                    "latest_period": max(cleaned_periods.keys())
                }
            else:
                statements_summary[stmt_type] = {
                    "available": False,
                    "periods_stored": 0,
                    "message": f"{stmt_type} not available from provider for {resolved_ticker}."
                }
        except Exception as e:
            statements_summary[stmt_type] = {
                "available": False,
                "periods_stored": 0,
                "message": f"Unavailable: {str(e)}"
            }

    # Prepare recent 5-day OHLCV preview for API response
    recent_ohlcv_preview = []
    if not cleaned_ohlcv_df.empty:
        for row in cleaned_ohlcv_df.tail(5).to_dict(orient="records"):
            recent_ohlcv_preview.append({
                "trade_date": row["trade_date"].isoformat(),
                "open": row["open_price"],
                "high": row["high_price"],
                "low": row["low_price"],
                "close": row["close_price"],
                "volume": int(row["volume"]),
            })

    return {
        "status": "success",
        "metadata": {
            "company": company_record.company_name,
            "ticker_symbol": company_record.ticker_symbol,
            "exchange": company_record.exchange,
            "currency": company_record.currency,
            "data_source": DATA_SOURCE_NAME,
            "retrieved_at": retrieved_timestamp,
        },
        "company_profile": {
            "sector": company_record.sector,
            "industry": company_record.industry,
            "website": company_record.website,
            "market_cap": company_record.market_cap,
            "description_preview": (company_record.description or "")[:200] + "..."
        },
        "ohlcv_collection": {
            "period_requested": yf_period,
            "records_stored_in_db": prices_stored_count,
            "validation_report": validation_report,
            "latest_5_sessions": recent_ohlcv_preview
        },
        "financial_statements": statements_summary
    }