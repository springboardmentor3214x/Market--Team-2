from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.watchlist import WatchlistCreate, WatchlistItem
from backend.app.crud.crud_watchlist import (
    add_to_watchlist,
    get_user_watchlist,
    remove_from_watchlist
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[WatchlistItem])
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the saved stocks watchlist for the currently logged-in user.
    """
    items = get_user_watchlist(db, current_user.user_id)
    return [
        {
            "id": str(item.watchlist_id),
            "watchlist_id": str(item.watchlist_id),
            "symbol": item.ticker_symbol,
            "ticker_symbol": item.ticker_symbol,
            "company_name": item.company_name,
            "exchange": item.exchange,
            "added_at": item.added_at
        }
        for item in items
    ]

@router.post("", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
def create_watchlist_item(
    item_in: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds a new stock to the logged-in user's watchlist.
    """
    symbol = item_in.symbol or item_in.ticker_symbol
    if not symbol or not symbol.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol is required"
        )

    ticker = symbol.upper().strip()
    company = item_in.company_name or ticker
    exchange = item_in.exchange or "NSE"

    saved_item = add_to_watchlist(
        db=db,
        user_id=current_user.user_id,
        ticker_symbol=ticker,
        company_name=company,
        exchange=exchange
    )

    if not saved_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock {ticker} is already in your watchlist."
        )

    return {
        "id": str(saved_item.watchlist_id),
        "watchlist_id": str(saved_item.watchlist_id),
        "symbol": saved_item.ticker_symbol,
        "ticker_symbol": saved_item.ticker_symbol,
        "company_name": saved_item.company_name,
        "exchange": saved_item.exchange,
        "added_at": saved_item.added_at
    }

@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
def delete_watchlist_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a stock from the logged-in user's watchlist (by item ID or ticker).
    """
    success = remove_from_watchlist(db, current_user.user_id, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your watchlist"
        )

    return {"message": "Stock successfully removed from watchlist"}
