from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from db.database import Base


class NotificationModel(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, default="INFO")
    title = Column(String, default="")
    message = Column(String, default="")
    channel = Column(String, default="log")
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
