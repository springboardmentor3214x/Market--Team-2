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
from backend.app.crud.crud_module3 import (
    create_research_task, get_research_task, get_research_tasks_by_user,
    update_task_status, upsert_agent_result, get_agent_result,
    get_all_agent_results_for_task, bulk_save_source_documents,
    save_research_report, get_report_by_task,
)