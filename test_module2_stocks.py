import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.db.session import SessionLocal
from backend.app.models.market_data import StockMetadata, HistoricalPrice

client = TestClient(app)

def test_stock_search():
    response = client.get("/stocks/search?query=INFY")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 0
    tickers = [r["ticker"] for r in results]
    assert any("INFY" in t for t in tickers)

def test_get_stock_data_infy_validation_and_db_caching():
    # Test retrieving INFY stock data
    response = client.get("/stocks/INFY?period=1mo")
    assert response.status_code == 200
    data = response.json()

    # 1. Metadata check
    assert data["ticker"] == "INFY"
    meta = data["metadata"]
    assert meta["current_price"] > 0
    assert meta["data_source"] in ["Alpha Vantage", "Yahoo Finance"]

    # 2. Pandas Validation Report check
    report = data["validation_report"]
    assert report["status"] == "VALIDATED"
    assert report["valid_records"] > 0
    assert report["anomalies_detected"] >= 0

    # 3. OHLCV series check
    history = data["historical_data"]
    assert len(history) > 0
    first_candle = history[0]
    assert "open" in first_candle
    assert "high" in first_candle
    assert "low" in first_candle
    assert "close" in first_candle
    assert "volume" in first_candle
    assert first_candle["high"] >= first_candle["low"]

    # 4. Verify PostgreSQL / DB Persistence
    db = SessionLocal()
    try:
        db_meta = db.query(StockMetadata).filter(StockMetadata.ticker == "INFY").first()
        assert db_meta is not None
        assert db_meta.current_price > 0

        db_candles = db.query(HistoricalPrice).filter(HistoricalPrice.ticker == "INFY").all()
        assert len(db_candles) > 0
    finally:
        db.close()

def test_get_stock_history_endpoint():
    response = client.get("/stocks/INFY/historical?period=1mo")
    assert response.status_code == 200
    series = response.json()
    assert isinstance(series, list)
    assert len(series) > 0

def test_get_stock_quote_endpoint():
    response = client.get("/stocks/INFY/quote")
    assert response.status_code == 200
    quote = response.json()
    assert quote["ticker"] == "INFY"
    assert quote["current_price"] > 0
