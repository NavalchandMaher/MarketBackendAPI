from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func

from db.database import Base


class BacktestModel(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(String, unique=True, index=True)
    symbol = Column(String, default="BTCUSDT")
    timeframe = Column(String, default="5m")
    days = Column(Integer, default=365)
    result = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
