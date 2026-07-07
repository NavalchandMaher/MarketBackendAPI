from sqlalchemy import Boolean, Column, Float, Integer, String, JSON, DateTime
from sqlalchemy.sql import func

from db.database import Base


class StrategyModel(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    version = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)
    paper_mode = Column(Boolean, default=True)
    live_mode = Column(Boolean, default=False)
    priority = Column(Integer, default=1)
    symbol = Column(String, default="BTCUSDT")
    timeframe = Column(String, default="5m")
    risk_percent = Column(Float, default=1.0)
    tp = Column(Float, default=2.0)
    sl = Column(Float, default=1.0)
    indicator_parameters = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
