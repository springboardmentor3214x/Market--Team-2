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
import backend.app.models  # Register all models with Base.metadata
from backend.app.routers.auth import router as auth_router
from backend.app.routers.preferences import router as preferences_router
from backend.app.routers.watchlist import router as watchlist_router
from backend.app.routers.research import router as research_router

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Research AI - Module 1",
    description="User Authentication and Research Workspace API (FastAPI + PostgreSQL/SQLite + React)",
    version="1.0.0"
)

# Configure CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount routers directly at root for direct paths (/register, /login, /preferences, /watchlist, /research-history)
app.include_router(auth_router)
app.include_router(preferences_router)
app.include_router(watchlist_router)
app.include_router(research_router)

# 2. Mount routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")

# 3. Also mount auth router under /api/v1/auth and /api/auth for full backward compatibility
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(auth_router, prefix="/api/auth")

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "module": "Module 1: User Authentication & Research Workspace",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
