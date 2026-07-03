"""
Trade Model
Market AI V2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Trade:

    symbol: str

    timeframe: str

    signal: str

    strategy_name: str

    strategy_version: int

    entry_price: float

    stop_loss: float

    take_profit: float

    confidence: float

    quantity: float = 1.0

    status: str = "OPEN"

    exit_price: Optional[float] = None

    pnl: float = 0.0

    pnl_percent: float = 0.0

    result: Optional[str] = None

    market_regime: str = ""

    indicators: dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    closed_at: Optional[datetime] = None

    trade_id: Optional[str] = None

    notes: str = ""

    def close_trade(self, exit_price: float):

        self.exit_price = exit_price

        self.closed_at = datetime.utcnow()

        self.updated_at = datetime.utcnow()

        if self.signal == "BUY":

            self.pnl = round(exit_price - self.entry_price, 2)

        else:

            self.pnl = round(self.entry_price - exit_price, 2)

        self.pnl_percent = round((self.pnl / self.entry_price) * 100, 2)

        self.result = "WIN" if self.pnl > 0 else "LOSS"

        self.status = "CLOSED"

    def is_open(self):

        return self.status == "OPEN"

    def is_closed(self):

        return self.status == "CLOSED"

    def to_dict(self):

        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "signal": self.signal,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "confidence": self.confidence,
            "quantity": self.quantity,
            "status": self.status,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "result": self.result,
            "market_regime": self.market_regime,
            "indicators": self.indicators,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data):

        return cls(
            trade_id=data.get("trade_id"),
            symbol=data.get("symbol"),
            timeframe=data.get("timeframe"),
            signal=data.get("signal"),
            strategy_name=data.get("strategy_name"),
            strategy_version=data.get("strategy_version", 1),
            entry_price=data.get("entry_price"),
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            confidence=data.get("confidence", 0),
            quantity=data.get("quantity", 1),
            status=data.get("status", "OPEN"),
            exit_price=data.get("exit_price"),
            pnl=data.get("pnl", 0),
            pnl_percent=data.get("pnl_percent", 0),
            result=data.get("result"),
            market_regime=data.get("market_regime", ""),
            indicators=data.get("indicators", {}),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            closed_at=data.get("closed_at"),
            notes=data.get("notes", ""),
        )
