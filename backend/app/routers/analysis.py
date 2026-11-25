
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db

from backend.app.schemas.fundamental import (
    FundamentalAnalysisRequest,
    FundamentalAnalysisResponse,
)
from backend.app.schemas.technical import (
    TechnicalAnalysisRequest,
    TechnicalAnalysisResponse,
)
from backend.app.schemas.news import (
    NewsAnalysisRequest,
    NewsAnalysisResponse,
)
from backend.app.schemas.risk import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
)

from backend.app.services.fundamental_agent import fundamental_agent
from backend.app.services.technical_agent import technical_agent
from backend.app.services.news_agent import news_agent
from backend.app.services.risk_agent import risk_agent

from backend.app.services.market_data import market_service

from backend.app.validators.financial_validators import (
    validate_ohlcv_data,
    validate_financial_statement,
)
from backend.app.services.fundamental_agent import run_fundamental_from_db

router = APIRouter(
    prefix="/analysis",
    tags=["Module 3 - Financial Analysis"]
)


@router.post(
    "/fundamental",
    response_model=FundamentalAnalysisResponse
)
def analyze_fundamentals(payload: FundamentalAnalysisRequest):
    """Run Fundamental Agent analysis."""

    financial_data = {
        "revenue": payload.revenue,
        "net_income": payload.net_income,
        "total_assets": payload.total_assets,
        "total_debt": payload.total_debt,
    }

    validation = validate_financial_statement(financial_data)

    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation["errors"]
        )

    return fundamental_agent.analyze(payload)

@router.get(
    "/fundamental/{ticker}",
    response_model=FundamentalAnalysisResponse,
    summary="Automatic DB-driven fundamental analysis"
)
def analyze_fundamentals_db(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Fully automatic fundamental analysis — just provide the ticker symbol.
    Fetches financial data from the database automatically.

    Example calls:
      GET /analysis/fundamental/INFY.NS
      GET /analysis/fundamental/TCS.NS
      GET /analysis/fundamental/RELIANCE.NS

    Prerequisites:
      Run POST /stocks/fetch/{ticker} first if data_limitations appear
      in the response — that call populates the database with market data.
    """
    try:
        return run_fundamental_from_db(db, ticker)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fundamental analysis error: {str(e)}"
        )
@router.post(
    "/technical",
    response_model=TechnicalAnalysisResponse
)
def analyze_technical(
    payload: TechnicalAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Fetch Module 2 historical data and run Technical Agent."""

    try:
        stock_data = market_service.get_stock_data_and_cache(
            db,
            payload.ticker,
            period=payload.period
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve stock market data."
        ) from exc

    historical_data = stock_data.get("historical_data", [])

    if not historical_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No historical data found for {payload.ticker}."
        )

    validation = validate_ohlcv_data(historical_data)

    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation["errors"]
        )

    return technical_agent.analyze(
        payload,
        historical_data
    )


@router.post(
    "/news",
    response_model=NewsAnalysisResponse
)
def analyze_news(payload: NewsAnalysisRequest):
    """Run News and Sentiment Agent analysis on supplied articles."""

    return news_agent.analyze(payload)


@router.post(
    "/risk",
    response_model=RiskAnalysisResponse
)
def analyze_risk(payload: RiskAnalysisRequest):
    """Run Risk Agent analysis."""

    return risk_agent.analyze(payload)
