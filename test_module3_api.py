
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.db.session import get_db
from backend.app.services.market_data import market_service


# Use a dummy database dependency because market data is mocked in these tests.
def override_get_db():
    yield None


@pytest.fixture
def client():
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


# -------------------------------
# Fundamental Agent API tests
# -------------------------------

def test_fundamental_analysis_success(client):
    payload = {
        "ticker": "INFY",
        "company_name": "Infosys",
        "revenue": 150000,
        "net_income": 25000,
        "total_assets": 300000,
        "total_debt": 50000,
        "shareholders_equity": 200000,
        "pe_ratio": 24,
        "pb_ratio": 5
    }

    response = client.post("/analysis/fundamental", json=payload)

    assert response.status_code == 200
    assert response.json()["ticker"] == "INFY"
    assert response.json()["roe"] == 12.5


def test_fundamental_invalid_revenue(client):
    payload = {
        "ticker": "INFY",
        "revenue": -100
    }

    response = client.post("/analysis/fundamental", json=payload)

    assert response.status_code == 422


# -------------------------------
# Technical Agent API tests
# -------------------------------

def sample_stock_data():
    records = []
    start_date = date(2026, 1, 1)

    for i in range(40):
        close = 100 + i

        records.append({
            "date": str(start_date + timedelta(days=i)),
            "open": close - 1,
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "volume": 1000
        })

    return records


def test_technical_analysis_success(client, monkeypatch):
    monkeypatch.setattr(
        market_service,
        "get_stock_data_and_cache",
        lambda db, ticker, period: {
            "historical_data": sample_stock_data()
        }
    )

    response = client.post(
        "/analysis/technical",
        json={"ticker": "INFY", "period": "6mo"}
    )

    assert response.status_code == 200
    assert response.json()["ticker"] == "INFY"
    assert response.json()["sma"] is not None
    assert response.json()["rsi"] is not None


def test_technical_no_market_data(client, monkeypatch):
    monkeypatch.setattr(
        market_service,
        "get_stock_data_and_cache",
        lambda db, ticker, period: {"historical_data": []}
    )

    response = client.post(
        "/analysis/technical",
        json={"ticker": "INFY"}
    )

    assert response.status_code == 404


def test_technical_market_data_failure(client, monkeypatch):
    def raise_error(db, ticker, period):
        raise Exception("Market data unavailable")

    monkeypatch.setattr(
        market_service,
        "get_stock_data_and_cache",
        raise_error
    )

    response = client.post(
        "/analysis/technical",
        json={"ticker": "INFY"}
    )

    assert response.status_code == 502


# -------------------------------
# News Agent API tests
# -------------------------------

def test_news_analysis_success(client):
    payload = {
        "ticker": "INFY",
        "articles": [
            {
                "headline": "Company reports strong growth",
                "source": "Test Source",
                "published_at": "2026-11-20",
                "sentiment": "positive"
            },
            {
                "headline": "Company faces market challenges",
                "source": "Test Source",
                "published_at": "2026-11-20",
                "sentiment": "negative"
            }
        ]
    }

    response = client.post("/analysis/news", json=payload)

    assert response.status_code == 200
    assert response.json()["ticker"] == "INFY"
    assert response.json()["overall_sentiment"] == "mixed"
    assert response.json()["total_articles"] == 2


def test_news_without_articles(client):
    response = client.post(
        "/analysis/news",
        json={"ticker": "INFY", "articles": []}
    )

    assert response.status_code == 200
    assert response.json()["overall_sentiment"] == "insufficient_data"
    assert response.json()["total_articles"] == 0


# -------------------------------
# Risk Agent API tests
# -------------------------------

def test_risk_analysis_success(client):
    payload = {
        "ticker": "INFY",
        "historical_volatility": 25,
        "maximum_drawdown": 0.15,
        "financial_risks": ["Debt exposure"],
        "sector_risks": ["Market competition"]
    }

    response = client.post("/analysis/risk", json=payload)

    assert response.status_code == 200
    assert response.json()["ticker"] == "INFY"
    assert response.json()["risk_level"] == "moderate"


def test_risk_without_numerical_data(client):
    response = client.post(
        "/analysis/risk",
        json={"ticker": "INFY"}
    )

    assert response.status_code == 200
    assert response.json()["risk_level"] == "undetermined"


def test_risk_invalid_volatility(client):
    response = client.post(
        "/analysis/risk",
        json={
            "ticker": "INFY",
            "historical_volatility": -10
        }
    )

    assert response.status_code == 422
