"""
Strategy Model
Market AI V2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Strategy:

    name: str

    version: int = 1

    enabled: bool = True

    description: str = ""

    # EMA Settings
    ema_fast: int = 20
    ema_slow: int = 50
    ema_long: int = 200

    # RSI
    rsi_buy: int = 40
    rsi_sell: int = 65

    # ADX
    adx_min: int = 25

    # Volume
    volume_ratio_min: float = 1.30

    # Signal Thresholds
    buy_threshold: int = 3
    sell_threshold: int = -3

    # Risk Management
    tp_percent: float = 2.0
    sl_percent: float = 1.0
    risk_reward: float = 2.0

    # Learning Engine
    learning_enabled: bool = True
    auto_optimize: bool = True

    # Performance
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    net_profit: float = 0.0
    max_drawdown: float = 0.0

    created_by: str = "SYSTEM"

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    notes: str = ""

    def update_performance(self, trades, wins, losses, net_profit, drawdown):

        self.total_trades = trades
        self.wins = wins
        self.losses = losses
        self.net_profit = net_profit
        self.max_drawdown = drawdown

        if trades > 0:
            self.win_rate = round((wins / trades) * 100, 2)

        self.updated_at = datetime.utcnow()

    def to_dict(self):

        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "description": self.description,
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "ema_long": self.ema_long,
            "rsi_buy": self.rsi_buy,
            "rsi_sell": self.rsi_sell,
            "adx_min": self.adx_min,
            "volume_ratio_min": self.volume_ratio_min,
            "buy_threshold": self.buy_threshold,
            "sell_threshold": self.sell_threshold,
            "tp_percent": self.tp_percent,
            "sl_percent": self.sl_percent,
            "risk_reward": self.risk_reward,
            "learning_enabled": self.learning_enabled,
            "auto_optimize": self.auto_optimize,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "net_profit": self.net_profit,
            "max_drawdown": self.max_drawdown,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data):

        return cls(
            name=data.get("name"),
            version=data.get("version", 1),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            ema_fast=data.get("ema_fast", 20),
            ema_slow=data.get("ema_slow", 50),
            ema_long=data.get("ema_long", 200),
            rsi_buy=data.get("rsi_buy", 40),
            rsi_sell=data.get("rsi_sell", 65),
            adx_min=data.get("adx_min", 25),
            volume_ratio_min=data.get("volume_ratio_min", 1.30),
            buy_threshold=data.get("buy_threshold", 3),
            sell_threshold=data.get("sell_threshold", -3),
            tp_percent=data.get("tp_percent", 2),
            sl_percent=data.get("sl_percent", 1),
            risk_reward=data.get("risk_reward", 2),
            learning_enabled=data.get("learning_enabled", True),
            auto_optimize=data.get("auto_optimize", True),
            total_trades=data.get("total_trades", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            win_rate=data.get("win_rate", 0),
            profit_factor=data.get("profit_factor", 0),
            net_profit=data.get("net_profit", 0),
            max_drawdown=data.get("max_drawdown", 0),
            created_by=data.get("created_by", "SYSTEM"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            notes=data.get("notes", ""),
        )
