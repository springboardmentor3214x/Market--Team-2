
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TechnicalAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=20)
    period: Literal["1mo", "3mo", "6mo", "1y", "2y"] = "6mo"

    sma_period: int = Field(default=20, ge=2, le=200)
    ema_period: int = Field(default=20, ge=2, le=200)
    rsi_period: int = Field(default=14, ge=2, le=50)


class TechnicalAnalysisResponse(BaseModel):
    ticker: str

    sma: Optional[float] = None
    ema: Optional[float] = None
    rsi: Optional[float] = None

    macd: Optional[float] = None
    macd_signal: Optional[float] = None

    historical_volatility: Optional[float] = None

    signal: Literal["bullish", "bearish", "neutral", "insufficient_data"]

    explanation: Optional[str] = None

    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
