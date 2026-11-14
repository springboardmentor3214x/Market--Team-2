import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from backend.app.db.session import Base, GUID, JSONType

class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(
        JSONType,
        nullable=False,
        default=lambda: {"preferred_market": "NSE", "analysis_period": "1Y"}
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    watchlist_items = relationship(
        "Watchlist",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    research_history = relationship(
        "ResearchHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"
