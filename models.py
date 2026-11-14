import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(
        JSONB,
        nullable=False,
        default=lambda: {"preferred_market": "NSE", "analysis_period": "1Y"}
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships: Connects User to their Watchlist and Research History
    # cascade="all, delete-orphan" ensures workspace items are deleted if the User is deleted
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    research_history = relationship("ResearchHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


class Watchlist(Base):
    __tablename__ = "watchlists"

    watchlist_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key linking to users.user_id with ON DELETE CASCADE
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    ticker_symbol = Column(String(50), nullable=False)   # e.g., "RELIANCE.NS", "TCS.NS"
    company_name = Column(String(255), nullable=True)    # e.g., "Reliance Industries"
    exchange = Column(String(50), default="NSE")         # e.g., "NSE", "BSE", "NASDAQ"
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="watchlist_items")

    # Constraint: A user cannot add the same stock ticker twice
    __table_args__ = (
        UniqueConstraint("user_id", "ticker_symbol", name="uq_user_watchlist_ticker"),
    )

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, ticker={self.ticker_symbol})>"


class ResearchHistory(Base):
    __tablename__ = "research_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key linking to users.user_id with ON DELETE CASCADE
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    ticker_symbol = Column(String(50), nullable=False)   # e.g., "TATAMOTORS.NS", "INFY.NS"
    company_name = Column(String(255), nullable=True)    # e.g., "Tata Motors"
    analysis_period = Column(String(50), nullable=True)  # e.g., "1Y", "5Y"
    research_summary = Column(JSONB, nullable=True)      # Can store report links/AI summary later
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User", back_populates="research_history")

    def __repr__(self):
        return f"<ResearchHistory(user_id={self.user_id}, ticker={self.ticker_symbol})>"