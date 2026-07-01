from pydantic import BaseModel
from datetime import datetime

class Trade(BaseModel):
    symbol: str
    side: str
    entry_price: float
    quantity: float
    status: str = "OPEN"
    created_at: datetime = datetime.utcnow()