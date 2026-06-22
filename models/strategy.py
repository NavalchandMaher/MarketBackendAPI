from pydantic import BaseModel

class Strategy(BaseModel):
    name: str
    enabled: bool = True
    timeframe: str