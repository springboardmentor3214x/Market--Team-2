
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class NewsArticle(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    headline: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., min_length=1, max_length=200)
    published_at: str = Field(..., min_length=1)
    url: Optional[HttpUrl] = None

    sentiment: Literal["positive", "negative", "neutral"]
    summary: Optional[str] = None


class NewsAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    articles: List[NewsArticle] = Field(default_factory=list)


class NewsAnalysisResponse(BaseModel):
    ticker: str

    overall_sentiment: Literal[
        "positive", "negative", "neutral", "mixed", "insufficient_data"
    ]

    total_articles: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)

    key_events: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

    conflicting_reports: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
