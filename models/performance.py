"""
Performance Model
Market AI V2
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Performance:

    date: str

    strategy_name: str

    strategy_version: int = 1

    total_trades: int = 0

    winning_trades: int = 0

    losing_trades: int = 0

    win_rate: float = 0.0

    gross_profit: float = 0.0

    gross_loss: float = 0.0

    net_profit: float = 0.0

    average_profit: float = 0.0

    average_loss: float = 0.0

    largest_win: float = 0.0

    largest_loss: float = 0.0

    profit_factor: float = 0.0

    expectancy: float = 0.0

    sharpe_ratio: float = 0.0

    max_drawdown: float = 0.0

    current_balance: float = 100000.0

    initial_balance: float = 100000.0

    roi: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    notes: str = ""

    def calculate_metrics(self):

        if self.total_trades > 0:

            self.win_rate = round((self.winning_trades / self.total_trades) * 100, 2)

        if self.winning_trades > 0:

            self.average_profit = round(self.gross_profit / self.winning_trades, 2)

        if self.losing_trades > 0:

            self.average_loss = round(self.gross_loss / self.losing_trades, 2)

        if self.gross_loss > 0:

            self.profit_factor = round(self.gross_profit / self.gross_loss, 2)

        self.net_profit = round(self.gross_profit - self.gross_loss, 2)

        self.current_balance = round(self.initial_balance + self.net_profit, 2)

        self.roi = round((self.net_profit / self.initial_balance) * 100, 2)

        self.updated_at = datetime.utcnow()

    def to_dict(self):

        return {
            "date": self.date,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "gross_profit": self.gross_profit,
            "gross_loss": self.gross_loss,
            "net_profit": self.net_profit,
            "average_profit": self.average_profit,
            "average_loss": self.average_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "current_balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "roi": self.roi,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data):

        return cls(
            date=data.get("date"),
            strategy_name=data.get("strategy_name"),
            strategy_version=data.get("strategy_version", 1),
            total_trades=data.get("total_trades", 0),
            winning_trades=data.get("winning_trades", 0),
            losing_trades=data.get("losing_trades", 0),
            win_rate=data.get("win_rate", 0),
            gross_profit=data.get("gross_profit", 0),
            gross_loss=data.get("gross_loss", 0),
            net_profit=data.get("net_profit", 0),
            average_profit=data.get("average_profit", 0),
            average_loss=data.get("average_loss", 0),
            largest_win=data.get("largest_win", 0),
            largest_loss=data.get("largest_loss", 0),
            profit_factor=data.get("profit_factor", 0),
            expectancy=data.get("expectancy", 0),
            sharpe_ratio=data.get("sharpe_ratio", 0),
            max_drawdown=data.get("max_drawdown", 0),
            current_balance=data.get("current_balance", 100000),
            initial_balance=data.get("initial_balance", 100000),
            roi=data.get("roi", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            notes=data.get("notes", ""),
        )
