import datetime
import urllib.request
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.market_data import StockMetadata, HistoricalPrice

logger = logging.getLogger(__name__)

class MarketDataService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY

    def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search companies using Alpha Vantage SYMBOL_SEARCH with fallback.
        """
        query = query.strip().upper()
        results = []

        # 1. Try Alpha Vantage Symbol Search
        try:
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={self.api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "MarketResearchAI/1.0"})
            with urllib.request.urlopen(req, timeout=7) as response:
                data = json.loads(response.read().decode())
                matches = data.get("bestMatches", [])
                for m in matches:
                    results.append({
                        "ticker": m.get("1. symbol"),
                        "name": m.get("2. name"),
                        "type": m.get("3. type", "Equity"),
                        "region": m.get("4. region", "Global"),
                        "currency": m.get("8. currency", "USD")
                    })
        except Exception as e:
            logger.warning(f"Alpha Vantage symbol search failed: {e}")

        # 2. Add common known Indian & US benchmarks if query matches
        popular_stocks = [
            {"ticker": "INFY", "name": "Infosys Ltd (NYSE)", "type": "Equity", "region": "United States", "currency": "USD"},
            {"ticker": "INFY.NS", "name": "Infosys Limited (NSE)", "type": "Equity", "region": "India", "currency": "INR"},
            {"ticker": "RELIANCE.NS", "name": "Reliance Industries Limited (NSE)", "type": "Equity", "region": "India", "currency": "INR"},
            {"ticker": "TCS.NS", "name": "Tata Consultancy Services (NSE)", "type": "Equity", "region": "India", "currency": "INR"},
            {"ticker": "HDFCBANK.NS", "name": "HDFC Bank Limited (NSE)", "type": "Equity", "region": "India", "currency": "INR"},
            {"ticker": "TATAMOTORS.NS", "name": "Tata Motors Ltd (NSE)", "type": "Equity", "region": "India", "currency": "INR"}
        ]
        
        for stock in popular_stocks:
            if query in stock["ticker"] or query.lower() in stock["name"].lower():
                if not any(r["ticker"] == stock["ticker"] for r in results):
                    results.insert(0, stock)

        return results

    def fetch_alpha_vantage_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches GLOBAL_QUOTE from Alpha Vantage.
        """
        # Strip exchange suffix for Alpha Vantage US if applicable
        symbol = ticker.split(".")[0] if "." in ticker and ticker.endswith((".NS", ".BO", ".BSE")) else ticker
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MarketResearchAI/1.0"})
            with urllib.request.urlopen(req, timeout=7) as response:
                data = json.loads(response.read().decode())
                gq = data.get("Global Quote", {})
                if gq and "05. price" in gq:
                    price = float(gq.get("05. price", 0))
                    prev_close = float(gq.get("08. previous close", price))
                    change = float(gq.get("09. change", 0))
                    change_pct_str = gq.get("10. change percent", "0%").replace("%", "")
                    change_pct = float(change_pct_str) if change_pct_str else 0.0

                    return {
                        "ticker": ticker,
                        "current_price": round(price, 2),
                        "open": float(gq.get("02. open", price)),
                        "high": float(gq.get("03. high", price)),
                        "low": float(gq.get("04. low", price)),
                        "volume": int(gq.get("06. volume", 0)),
                        "previous_close": round(prev_close, 2),
                        "price_change": round(change, 2),
                        "price_change_percent": round(change_pct, 2),
                        "data_source": "Alpha Vantage",
                        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
        except Exception as e:
            logger.warning(f"Alpha Vantage quote failed for {ticker}: {e}")
        return None

    def fetch_alpha_vantage_history(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Fetches TIME_SERIES_DAILY from Alpha Vantage.
        """
        symbol = ticker.split(".")[0] if "." in ticker and ticker.endswith((".NS", ".BO", ".BSE")) else ticker
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MarketResearchAI/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode())
                ts = data.get("Time Series (Daily)", {})
                if not ts:
                    return None

                records = []
                for date_str, metrics in ts.items():
                    records.append({
                        "date": pd.to_datetime(date_str).date(),
                        "open": float(metrics["1. open"]),
                        "high": float(metrics["2. high"]),
                        "low": float(metrics["3. low"]),
                        "close": float(metrics["4. close"]),
                        "volume": int(metrics["5. volume"])
                    })
                df = pd.DataFrame(records)
                return df
        except Exception as e:
            logger.warning(f"Alpha Vantage history failed for {ticker}: {e}")
        return None

    def fetch_yfinance_data(self, ticker: str, period: str = "3mo") -> Dict[str, Any]:
        """
        Fallback / Complementary provider using yfinance.
        """
        import yfinance as yf
        # Map common Indian tickers
        formatted_ticker = ticker
        if not ticker.endswith((".NS", ".BO")) and ticker in ["INFY", "TCS", "RELIANCE", "HDFCBANK", "TATAMOTORS"]:
            # Check if user prefers NSE or standard
            pass

        t = yf.Ticker(formatted_ticker)
        hist = t.history(period=period)
        info = t.info or {}

        records = []
        if not hist.empty:
            for idx, row in hist.iterrows():
                dt = idx.date() if hasattr(idx, "date") else pd.to_datetime(idx).date()
                records.append({
                    "date": dt,
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0))
                })

        df = pd.DataFrame(records)

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        if not current_price and records:
            current_price = records[-1]["close"]
            prev_close = records[-2]["close"] if len(records) > 1 else current_price

        change = round(current_price - prev_close, 2) if (current_price and prev_close) else 0.0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        quote = {
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "exchange": info.get("exchange", "NSE" if ".NS" in ticker else "NYSE"),
            "currency": info.get("currency", "INR" if ".NS" in ticker else "USD"),
            "current_price": round(current_price, 2) if current_price else 0.0,
            "previous_close": round(prev_close, 2) if prev_close else 0.0,
            "price_change": change,
            "price_change_percent": change_pct,
            "open": float(records[-1]["open"]) if records else 0.0,
            "high": float(records[-1]["high"]) if records else 0.0,
            "low": float(records[-1]["low"]) if records else 0.0,
            "volume": int(records[-1]["volume"]) if records else 0,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "data_source": "Yahoo Finance",
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        return {"quote": quote, "df": df}

    def validate_and_organize_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Organize and validate stock data using Pandas:
        - Checks missing values
        - Removes duplicate dates
        - Sorts chronologically
        - Validates numerical integrity: High >= Low, High >= Open, High >= Close, Volume >= 0
        """
        if df.empty:
            return {
                "clean_df": pd.DataFrame(),
                "report": {
                    "total_records": 0,
                    "valid_records": 0,
                    "anomalies_detected": 0,
                    "missing_values_imputed": 0,
                    "duplicates_removed": 0,
                    "status": "EMPTY"
                }
            }

        total_initial = len(df)
        
        # 1. Remove duplicate dates
        df = df.drop_duplicates(subset=["date"]).copy()
        duplicates_removed = total_initial - len(df)

        # 2. Check & handle missing / null values
        missing_count = int(df[["open", "high", "low", "close", "volume"]].isna().sum().sum())
        # Impute missing prices using forward-fill then backward-fill
        df["close"] = df["close"].ffill().bfill()
        df["open"] = df["open"].fillna(df["close"])
        df["high"] = df["high"].fillna(df[["open", "close"]].max(axis=1))
        df["low"] = df["low"].fillna(df[["open", "close"]].min(axis=1))
        df["volume"] = df["volume"].fillna(0).astype(int)

        # 3. Sort chronologically
        df = df.sort_values(by="date", ascending=True).reset_index(drop=True)

        # 4. Numerical Logic Validation (High must be max, Low must be min)
        anomalies = 0
        for i in range(len(df)):
            o = df.at[i, "open"]
            h = df.at[i, "high"]
            l = df.at[i, "low"]
            c = df.at[i, "close"]

            # Fix inverted high/low if any
            if h < l:
                anomalies += 1
                df.at[i, "high"], df.at[i, "low"] = l, h
                h, l = df.at[i, "high"], df.at[i, "low"]

            if h < max(o, c):
                anomalies += 1
                df.at[i, "high"] = max(o, c)

            if l > min(o, c):
                anomalies += 1
                df.at[i, "low"] = min(o, c)

        validation_report = {
            "total_records": total_initial,
            "valid_records": len(df),
            "anomalies_detected": anomalies,
            "missing_values_imputed": missing_count,
            "duplicates_removed": duplicates_removed,
            "status": "VALIDATED"
        }

        return {
            "clean_df": df,
            "report": validation_report
        }

    def get_stock_data_and_cache(
        self,
        db: Session,
        ticker: str,
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """
        Coordinates Alpha Vantage + Fallback, runs Pandas validation, and persists to PostgreSQL.
        """
        ticker = ticker.strip().upper()
        
        # 1. Try Alpha Vantage first for quotes and history
        av_quote = self.fetch_alpha_vantage_quote(ticker)
        av_df = self.fetch_alpha_vantage_history(ticker)

        data_source = "Alpha Vantage"
        quote_data = av_quote
        history_df = av_df

        # If Alpha Vantage didn't return both (e.g. rate limit, Indian ticker), fallback to yfinance
        if quote_data is None or history_df is None or history_df.empty:
            yf_res = self.fetch_yfinance_data(ticker, period=period)
            data_source = "Yahoo Finance"
            quote_data = quote_data or yf_res.get("quote", {})
            history_df = yf_res.get("df", pd.DataFrame())

        # 2. Run Pandas Validation Pipeline
        validated = self.validate_and_organize_data(history_df)
        clean_df = validated["clean_df"]
        report = validated["report"]

        # 3. Store / Cache Metadata in PostgreSQL
        existing_meta = db.query(StockMetadata).filter(StockMetadata.ticker == ticker).first()
        if not existing_meta:
            existing_meta = StockMetadata(ticker=ticker)
            db.add(existing_meta)

        existing_meta.name = quote_data.get("name") or (existing_meta.name or ticker)
        existing_meta.exchange = quote_data.get("exchange") or existing_meta.exchange
        existing_meta.currency = quote_data.get("currency") or existing_meta.currency
        existing_meta.current_price = quote_data.get("current_price") or existing_meta.current_price
        existing_meta.price_change = quote_data.get("price_change") or existing_meta.price_change
        existing_meta.price_change_percent = quote_data.get("price_change_percent") or existing_meta.price_change_percent
        existing_meta.sector = quote_data.get("sector") or existing_meta.sector
        existing_meta.industry = quote_data.get("industry") or existing_meta.industry
        existing_meta.market_cap = quote_data.get("market_cap") or existing_meta.market_cap
        existing_meta.pe_ratio = quote_data.get("pe_ratio") or existing_meta.pe_ratio
        existing_meta.fifty_two_week_high = quote_data.get("fifty_two_week_high") or existing_meta.fifty_two_week_high
        existing_meta.fifty_two_week_low = quote_data.get("fifty_two_week_low") or existing_meta.fifty_two_week_low
        existing_meta.data_source = data_source
        existing_meta.retrieved_at = datetime.datetime.now(datetime.timezone.utc)

        # 4. Store / Upsert Historical Prices in PostgreSQL
        history_records = []
        if not clean_df.empty:
            for _, row in clean_df.iterrows():
                row_date = row["date"]
                record = {
                    "date": str(row_date),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(row["volume"])
                }
                history_records.append(record)

                # Upsert into PostgreSQL
                existing_hp = db.query(HistoricalPrice).filter(
                    HistoricalPrice.ticker == ticker,
                    HistoricalPrice.date == row_date
                ).first()

                if not existing_hp:
                    hp = HistoricalPrice(
                        ticker=ticker,
                        date=row_date,
                        open=record["open"],
                        high=record["high"],
                        low=record["low"],
                        close=record["close"],
                        volume=record["volume"],
                        data_source=data_source
                    )
                    db.add(hp)
                else:
                    existing_hp.open = record["open"]
                    existing_hp.high = record["high"]
                    existing_hp.low = record["low"]
                    existing_hp.close = record["close"]
                    existing_hp.volume = record["volume"]
                    existing_hp.data_source = data_source

        db.commit()

        return {
            "ticker": ticker,
            "metadata": {
                "ticker": ticker,
                "name": existing_meta.name,
                "exchange": existing_meta.exchange,
                "currency": existing_meta.currency,
                "sector": existing_meta.sector,
                "industry": existing_meta.industry,
                "market_cap": existing_meta.market_cap,
                "pe_ratio": existing_meta.pe_ratio,
                "current_price": existing_meta.current_price,
                "price_change": existing_meta.price_change,
                "price_change_percent": existing_meta.price_change_percent,
                "data_source": data_source,
                "retrieved_at": existing_meta.retrieved_at.isoformat() if existing_meta.retrieved_at else None
            },
            "validation_report": report,
            "historical_data": history_records
        }

market_service = MarketDataService()
