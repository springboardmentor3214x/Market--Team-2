from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.preferences import PreferencesUpdate, PreferencesResponse
from backend.app.crud.crud_user import update_user_preferences

router = APIRouter(prefix="/preferences", tags=["User Preferences"])

@router.get("", response_model=PreferencesResponse)
def get_preferences(current_user: User = Depends(get_current_user)):
    """
    Retrieves the preferences for the currently authenticated user.
    """
    prefs = current_user.preferences or {}
    market = prefs.get("preferred_market") or prefs.get("market", "NSE")
    period = prefs.get("analysis_period") or prefs.get("period", "3 months")

    return {
        "market": market,
        "period": period,
        "preferred_market": market,
        "analysis_period": period
    }

@router.put("", response_model=PreferencesResponse)
def update_preferences(
    prefs_in: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates preferences (preferred stock market and analysis period) for the user.
    """
    market = prefs_in.market or prefs_in.preferred_market or "NSE"
    period = prefs_in.period or prefs_in.analysis_period or "3 months"

    new_prefs = {
        "preferred_market": market,
        "analysis_period": period,
        "market": market,
        "period": period
    }

    updated_user = update_user_preferences(db, current_user.user_id, new_prefs)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "market": market,
        "period": period,
        "preferred_market": market,
        "analysis_period": period
    }
