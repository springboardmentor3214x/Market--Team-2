from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WatchlistCreate(BaseModel):
    # Support both 'symbol' (frontend) and 'ticker_symbol' (DB)
    symbol: Optional[str] = None
    ticker_symbol: Optional[str] = None
    company_name: Optional[str] = None
    exchange: Optional[str] = "NSE"

class WatchlistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    watchlist_id: str
    symbol: str
    ticker_symbol: str
    company_name: Optional[str] = None
    exchange: Optional[str] = "NSE"
    added_at: datetime
