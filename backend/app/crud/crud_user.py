import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.user import User

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Looks up a user by email (case-insensitive and trimmed).
    """
    return db.query(User).filter(User.email == email.lower().strip()).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """
    Retrieves a user by their UUID.
    """
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(
    db: Session,
    email: str,
    password_hash: str,
    preferences: Optional[Dict[str, Any]] = None
) -> User:
    """
    Inserts a newly registered user with their hashed password and default preferences.
    """
    default_prefs = preferences or {"preferred_market": "NSE", "analysis_period": "1Y"}
    new_user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        preferences=default_prefs
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user_preferences(
    db: Session,
    user_id: uuid.UUID,
    new_preferences: Dict[str, Any]
) -> Optional[User]:
    """
    Updates the preferences JSON for a given user.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    updated_prefs = dict(user.preferences or {})
    updated_prefs.update(new_preferences)
    user.preferences = updated_prefs
    db.commit()
    db.refresh(user)
    return user
