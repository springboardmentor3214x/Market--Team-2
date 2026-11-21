
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class RiskAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=20)

    historical_volatility: Optional[float] = Field(None, ge=0)
    maximum_drawdown: Optional[float] = Field(None, ge=0, le=1)

    financial_risks: List[str] = Field(default_factory=list)
    sector_risks: List[str] = Field(default_factory=list)

    agent_conflicts: List[str] = Field(default_factory=list)

    missing_data: List[str] = Field(default_factory=list)


class RiskAnalysisResponse(BaseModel):
    ticker: str

    risk_level: Literal[
        "low", "moderate", "high", "very_high", "undetermined"
    ]

    historical_volatility: Optional[float] = None
    maximum_drawdown: Optional[float] = None

    major_risks: List[str] = Field(default_factory=list)
    alternative_scenarios: List[str] = Field(default_factory=list)

    agent_conflicts: List[str] = Field(default_factory=list)

    explanation: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
