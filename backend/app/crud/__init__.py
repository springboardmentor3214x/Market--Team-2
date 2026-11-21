from backend.app.crud.crud_user import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user_preferences
)
from backend.app.crud.crud_watchlist import (
    add_to_watchlist,
    get_user_watchlist,
    remove_from_watchlist
)
from backend.app.crud.crud_research import (
    log_research_activity,
    get_user_research_history
)

__all__ = [
    "get_user_by_email",
    "get_user_by_id",
    "create_user",
    "update_user_preferences",
    "add_to_watchlist",
    "get_user_watchlist",
    "remove_from_watchlist",
    "log_research_activity",
    "get_user_research_history"
]
