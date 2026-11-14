from pydantic import BaseModel
from typing import Optional

class PreferencesUpdate(BaseModel):
    # Support both frontend format (market, period) and database format (preferred_market, analysis_period)
    market: Optional[str] = None
    period: Optional[str] = None
    preferred_market: Optional[str] = None
    analysis_period: Optional[str] = None

class PreferencesResponse(BaseModel):
    market: str
    period: str
    preferred_market: str
    analysis_period: str
