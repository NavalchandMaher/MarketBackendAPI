from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func

from db.database import Base


class PaperTradeModel(Base):
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, unique=True, index=True)
    symbol = Column(String, default="BTCUSDT")
    timeframe = Column(String, default="5m")
    strategy = Column(String, default="DEFAULT")
    signal = Column(String, default="BUY")
    entry = Column(Float, default=0.0)
    exit_price = Column(Float, default=0.0)
    tp = Column(Float, default=0.0)
    sl = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    duration = Column(Integer, default=0)
    reason = Column(String, default="")
    status = Column(String, default="OPEN")
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
