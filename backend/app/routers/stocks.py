import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.core.security import decode_access_token
from backend.app.crud.crud_research import log_research_activity
from backend.app.schemas.market_data import StockSearchResult, StockDetailResponse, OHLCVItem, StockMetadataSchema
from backend.app.services.market_data import market_service

router = APIRouter(prefix="/stocks", tags=["Stock Market Data"])

@router.get("/search", response_model=List[StockSearchResult])
def search_companies(query: str = Query(..., min_length=1, description="Company name or ticker symbol")):
    """
    Module 2: Search for companies using their name or ticker symbol.
    Integrates Alpha Vantage SYMBOL_SEARCH with benchmark presets.
    """
    results = market_service.search_stocks(query)
    return results

@router.get("/{ticker}", response_model=StockDetailResponse)
def get_stock_data(
    ticker: str,
    request: Request,
    period: str = Query("3mo", description="Historical period: 1mo, 3mo, 6mo, 1y"),
    db: Session = Depends(get_db)
):
    """
    Module 2: Retrieve stock data, validate with Pandas, store in PostgreSQL, and return clean OHLCV.
    Automatically logs research activity if an authenticated user is calling.
    """
    data = market_service.get_stock_data_and_cache(db, ticker, period=period)
    if not data or not data.get("metadata", {}).get("current_price"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not retrieve stock data for ticker '{ticker}'"
        )

    # Automatically record research activity if user is authenticated
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            try:
                user_id = uuid.UUID(payload["sub"])
                meta = data.get("metadata", {})
                log_research_activity(
                    db=db,
                    user_id=user_id,
                    ticker_symbol=ticker.upper().strip(),
                    company_name=meta.get("name") or ticker,
                    analysis_period=period,
                    research_summary={
                        "price": meta.get("current_price"),
                        "change_percent": meta.get("price_change_percent"),
                        "source": meta.get("data_source")
                    }
                )
            except Exception:
                pass

    return data

@router.get("/{ticker}/historical", response_model=List[OHLCVItem])
def get_stock_history(
    ticker: str,
    period: str = Query("3mo", description="Historical period: 1mo, 3mo, 6mo, 1y"),
    db: Session = Depends(get_db)
):
    """
    Module 2: Retrieve Pandas-validated OHLCV historical price series.
    """
    data = market_service.get_stock_data_and_cache(db, ticker, period=period)
    return data.get("historical_data", [])

@router.get("/{ticker}/quote", response_model=StockMetadataSchema)
def get_stock_quote(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Module 2: Retrieve real-time/latest quote and metadata for a company.
    """
    data = market_service.get_stock_data_and_cache(db, ticker, period="1mo")
    return data.get("metadata")
