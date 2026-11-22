import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.news_agent import news_agent, NewsAgentService
from backend.app.schemas.news import NewsArticle, NewsAnalysisRequest
from database import SessionLocal
import models
import crud
import uuid

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_sentiment_classification():
    service = NewsAgentService()

    # Positive headline
    sentiment, score = service.classify_sentiment("Company reports surging quarterly profit and record dividend increase")
    assert sentiment == "positive"
    assert score > 0

    # Negative headline
    sentiment, score = service.classify_sentiment("Company faces steep decline in revenue amidst regulatory fraud investigation")
    assert sentiment == "negative"
    assert score < 0

    # Neutral headline
    sentiment, score = service.classify_sentiment("Company to hold annual general meeting on Thursday")
    assert sentiment == "neutral"


def test_corporate_event_detection():
    service = NewsAgentService()

    cat_earnings = service.detect_category("Infosys Q3 Results: Profit beats estimates, revenue jumps 8%")
    assert cat_earnings == "Earnings & Financials"

    cat_ma = service.detect_category("Tech Giant to acquire strategic stake in European cloud provider")
    assert cat_ma == "Mergers & Acquisitions (M&A)"

    cat_reg = service.detect_category("Regulator launches antitrust probe into pricing compliance")
    assert cat_reg == "Regulatory & Legal"

    cat_lead = service.detect_category("Board announces CEO resignation, appoints veteran executive")
    assert cat_lead == "Leadership & Governance"


def test_conflicting_reports_detection():
    request = NewsAnalysisRequest(
        ticker="INFY",
        articles=[
            NewsArticle(
                headline="Infosys wins multi-million dollar cloud deal, shares surge",
                source="Reuters",
                published_at="2026-11-20",
                url="https://example.com/1",
                sentiment="positive"
            ),
            NewsArticle(
                headline="Infosys faces margin compression as operating costs drop profitability",
                source="Bloomberg",
                published_at="2026-11-21",
                url="https://example.com/2",
                sentiment="negative"
            ),
            NewsArticle(
                headline="Rumors circulate of alleged leadership shakeup",
                source="Market Blog",
                published_at="2026-11-21",
                url="https://example.com/3",
                sentiment="neutral"
            )
        ]
    )

    result = news_agent.analyze(request)
    assert result.overall_sentiment == "mixed"
    assert result.positive_count == 1
    assert result.negative_count == 1
    assert result.neutral_count == 1
    assert len(result.conflicting_reports) >= 1
    # Check that uncertainty was flagged from "Rumors" / "alleged"
    assert any("Uncertainty detected" in cr or "divergent viewpoints" in cr for cr in result.conflicting_reports)


def test_news_agent_database_persistence(db):
    # Create a dummy user and task
    user = crud.create_user(db, email=f"news_test_{uuid.uuid4().hex[:6]}@example.com", password_hash="testpass")
    task = crud.create_research_task(db, user.user_id, ticker_symbol="INFY", market="NSE")

    request = NewsAnalysisRequest(
        ticker="INFY",
        task_id=str(task.task_id),
        articles=[
            NewsArticle(
                headline="Infosys expands generative AI services with European client",
                source="Business Standard",
                published_at="2026-11-21",
                url="https://example.com/ai-deal",
                sentiment="positive"
            )
        ]
    )

    response = news_agent.analyze(request, db=db)
    assert response.sources_saved >= 1

    # Verify agent_results in DB
    agent_res = crud.get_agent_result(db, task.task_id, models.AgentName.NEWS)
    assert agent_res is not None
    assert agent_res.status == models.AgentStatus.COMPLETED
    assert agent_res.output_json["overall_sentiment"] == "positive"


def test_api_get_live_news_endpoint(client):
    response = client.get("/analysis/news/INFY")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "INFY"
    assert "overall_sentiment" in data
    assert "total_articles" in data
    assert "articles" in data
