# backend/app/models/__init__.py

from backend.app.models.user import User
from backend.app.models.watchlist import Watchlist
from backend.app.models.research_history import ResearchHistory
from backend.app.models.market_data import StockMetadata, HistoricalPrice
from backend.app.models.research_models import (       # ← NEW
    ResearchTask, AgentResult, SourceDocument, ResearchReport,
    TaskStatus, AgentName, AgentStatus, SourceType
)

# Root-level models (Nisheeth's Module 2 — still used by backend)
from models import Company, StockPrice, FinancialStatement

__all__ = [
    # Auth & workspace
    "User",
    "Watchlist",
    "ResearchHistory",
    # Market data
    "StockMetadata",
    "HistoricalPrice",
    "Company",
    "StockPrice",
    "FinancialStatement",
    # Module 3 research pipeline
    "ResearchTask",
    "AgentResult",
    "SourceDocument",
    "ResearchReport",
    # Enums
    "TaskStatus",
    "AgentName",
    "AgentStatus",
    "SourceType",
]