from backend.app.routers.auth import router as auth_router
from backend.app.routers.preferences import router as preferences_router
from backend.app.routers.watchlist import router as watchlist_router
from backend.app.routers.research import router as research_router

__all__ = [
    "auth_router",
    "preferences_router",
    "watchlist_router",
    "research_router"
]
