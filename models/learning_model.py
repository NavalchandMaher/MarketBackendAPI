from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func

from db.database import Base


class LearningModel(Base):
    __tablename__ = "learning_history"

    id = Column(Integer, primary_key=True, index=True)
    old_parameters = Column(JSON, default={})
    new_parameters = Column(JSON, default={})
    reason = Column(String, default="")
    improvement = Column(String, default="")
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
