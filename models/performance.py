from pydantic import BaseModel

class Performance(BaseModel):
    total_trades: int
    wins: int
    losses: int
    pnl: float