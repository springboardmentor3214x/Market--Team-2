
import sys
import os

# Ensure project root is in sys.path regardless of execution directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

for p in [parent_dir, current_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.db.session import engine, Base

# Register all database models
import backend.app.models

# Module 1 routers
from backend.app.routers.auth import router as auth_router
from backend.app.routers.preferences import router as preferences_router
from backend.app.routers.watchlist import router as watchlist_router
from backend.app.routers.research import router as research_router

# Module 2 router
from backend.app.routers.stocks import router as stocks_router

# Module 3 router
from backend.app.routers.analysis import router as analysis_router


# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)


# Initialize FastAPI application
app = FastAPI(
    title="Market Research AI - Multi-Agent System",
    description=(
        "Stock Market Analysis & Multi-Agent Research Platform "
        "(FastAPI + PostgreSQL/SQLite + React)"
    ),
    version="1.2.0"
)


# Configure CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 1. Register routers directly at root
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(preferences_router)
app.include_router(watchlist_router)
app.include_router(research_router)
app.include_router(stocks_router)
app.include_router(analysis_router)


# --------------------------------------------------
# 2. Register routers under /api/v1
# --------------------------------------------------

app.include_router(auth_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")


# --------------------------------------------------
# 3. Authentication backward compatibility
# --------------------------------------------------

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(auth_router, prefix="/api/auth")


# --------------------------------------------------
# 4. Health check endpoints
# --------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "modules": [
            "Module 1: User Authentication & Research Workspace",
            "Module 2: Stock Search and Market Data Collection",
            "Module 3: Financial Analysis Tools and Individual AI Agents"
        ],
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok"
    }
