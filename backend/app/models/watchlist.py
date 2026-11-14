import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.app.db.session import Base, GUID

class Watchlist(Base):
    __tablename__ = "watchlists"

    watchlist_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker_symbol = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=True)
    exchange = Column(String(50), default="NSE")
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="watchlist_items")

    # Constraint: A user cannot add the same stock ticker twice
    __table_args__ = (
        UniqueConstraint("user_id", "ticker_symbol", name="uq_user_watchlist_ticker"),
    )

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, ticker={self.ticker_symbol})>"
