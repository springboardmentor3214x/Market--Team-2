from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class StockSearchResult(BaseModel):
    ticker: str
    name: Optional[str] = None
    type: Optional[str] = "Equity"
    region: Optional[str] = "Global"
    currency: Optional[str] = "USD"

class OHLCVItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class ValidationReport(BaseModel):
    total_records: int
    valid_records: int
    anomalies_detected: int
    missing_values_imputed: int
    duplicates_removed: int
    status: str

class StockMetadataSchema(BaseModel):
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = "INR"
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    current_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    data_source: str
    retrieved_at: Optional[str] = None

class StockDetailResponse(BaseModel):
    ticker: str
    metadata: StockMetadataSchema
    validation_report: ValidationReport
    historical_data: List[OHLCVItem]
