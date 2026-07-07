from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from db.database import Base


class TradingAccountModel(Base):
    __tablename__ = "trading_account"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=100000.0)
    leverage = Column(Integer, default=10)
    broker = Column(String, default="Binance")
    risk_percent = Column(Float, default=1.0)
    max_open_trades = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
