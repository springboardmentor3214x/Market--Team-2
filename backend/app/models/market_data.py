import uuid
from sqlalchemy import Column, String, Float, BigInteger, Date, DateTime, UniqueConstraint, func
from backend.app.db.session import Base, GUID, JSONType

class StockMetadata(Base):
    __tablename__ = "stock_metadata"

    ticker = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(50), nullable=True)
    currency = Column(String(20), default="INR")
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    fifty_two_week_high = Column(Float, nullable=True)
    fifty_two_week_low = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    price_change = Column(Float, nullable=True)
    price_change_percent = Column(Float, nullable=True)
    data_source = Column(String(50), default="Alpha Vantage")
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StockMetadata(ticker={self.ticker}, price={self.current_price})>"


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ticker = Column(String(50), index=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    data_source = Column(String(50), default="Alpha Vantage")
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_ticker_date"),
    )

    def __repr__(self):
        return f"<HistoricalPrice(ticker={self.ticker}, date={self.date}, close={self.close})>"
