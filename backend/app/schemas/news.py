from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NewsArticle(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    headline: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., min_length=1, max_length=200)
    published_at: str = Field(..., min_length=1)
    url: Optional[str] = None

    sentiment: Optional[Literal["positive", "negative", "neutral"]] = None
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    category: Optional[str] = Field(default=None, description="Event category e.g. Earnings, M&A, Regulatory, Leadership")
    summary: Optional[str] = None


class NewsAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    articles: Optional[List[NewsArticle]] = None
    auto_fetch: bool = Field(default=False, description="If True or articles omitted, fetches live news from permitted sources")
    task_id: Optional[str] = Field(default=None, description="Optional UUID of research_tasks to persist results & source_documents")


class CorporateEvent(BaseModel):
    event_type: str = Field(..., description="e.g. Earnings, M&A, Regulatory, Leadership, Partnership")
    headline: str
    source: str
    published_at: str
    url: Optional[str] = None
    summary: Optional[str] = None
    importance: Literal["high", "medium", "low"] = "medium"


class NewsAnalysisResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None

    overall_sentiment: Literal[
        "positive", "negative", "neutral", "mixed", "insufficient_data"
    ]
    sentiment_score: Optional[float] = Field(default=0.0, description="Normalized score from -1.0 (most negative) to +1.0 (most positive)")

    total_articles: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)

    key_events: List[str] = Field(default_factory=list)
    articles: List[NewsArticle] = Field(default_factory=list)
    corporate_events: List[CorporateEvent] = Field(default_factory=list)

    summary: Optional[str] = None
    conflicting_reports: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
    sources_saved: Optional[int] = Field(default=0, description="Count of source documents persisted to DB if task_id provided")
