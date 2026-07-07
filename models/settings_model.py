from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func

from db.database import Base


class SettingsModel(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String, default="dark")
    refresh_interval = Column(Integer, default=30)
    notifications = Column(Boolean, default=True)
    risk = Column(Float, default=1.0)
    default_symbol = Column(String, default="BTCUSDT")
    default_timeframe = Column(String, default="5m")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
