from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

class ResearchCreate(BaseModel):
    # Support both 'stock_symbol' (frontend) and 'ticker_symbol' (DB)
    ticker_symbol: Optional[str] = None
    stock_symbol: Optional[str] = None
    company_name: Optional[str] = None
    analysis_period: Optional[str] = "1Y"
    research_summary: Optional[Any] = None

class ResearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    history_id: str
    stock_symbol: str
    ticker_symbol: str
    company_name: Optional[str] = None
    analysis_period: Optional[str] = "1Y"
    research_summary: Optional[Any] = None
    created_at: str
    searched_at: str
