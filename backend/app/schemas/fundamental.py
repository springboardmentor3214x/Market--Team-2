
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FundamentalAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None

    revenue: Optional[float] = Field(None, ge=0)
    net_income: Optional[float] = None
    total_assets: Optional[float] = Field(None, ge=0)
    total_debt: Optional[float] = Field(None, ge=0)
    shareholders_equity: Optional[float] = Field(None, ge=0)

    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None


class FundamentalAnalysisResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None

    profitability_summary: Optional[str] = None
    financial_stability: Optional[str] = None

    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None

    historical_comparison: Optional[str] = None
    peer_comparison: Optional[str] = None

    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
