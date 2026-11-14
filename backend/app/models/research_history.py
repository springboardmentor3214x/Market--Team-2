import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.db.session import Base, GUID, JSONType

class ResearchHistory(Base):
    __tablename__ = "research_history"

    history_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker_symbol = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=True)
    analysis_period = Column(String(50), nullable=True)
    research_summary = Column(JSONType, nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="research_history")

    def __repr__(self):
        return f"<ResearchHistory(user_id={self.user_id}, ticker={self.ticker_symbol})>"
