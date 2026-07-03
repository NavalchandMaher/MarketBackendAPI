"""
Backtest Result Model
Market AI V2
"""

# {
#   "strategy_name": "EMA_MACD_V2",
#   "strategy_version": 5,
#   "symbol": "BTCUSDT",
#   "timeframe": "5m",
#   "start_date": "2025-07-01",
#   "end_date": "2026-07-01",
#   "initial_balance": 100000,
#   "final_balance": 143250,
#   "total_trades": 845,
#   "winning_trades": 603,
#   "losing_trades": 242,
#   "win_rate": 71.36,
#   "gross_profit": 81250,
#   "gross_loss": 38000,
#   "net_profit": 43250,
#   "roi": 43.25,
#   "profit_factor": 2.14,
#   "expectancy": 51.18,
#   "max_drawdown": 6.8,
#   "sharpe_ratio": 1.92,
#   "average_holding_minutes": 42,
#   "average_win": 134.74,
#   "average_loss": 157.02,
#   "largest_win": 1280,
#   "largest_loss": 520,
#   "created_at": "2026-07-02T09:30:00Z",
#   "notes": "Nightly automatic backtest"
# }


from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BacktestResult:

    strategy_name: str

    strategy_version: int

    symbol: str

    timeframe: str

    start_date: str

    end_date: str

    initial_balance: float = 100000.0

    final_balance: float = 100000.0

    total_trades: int = 0

    winning_trades: int = 0

    losing_trades: int = 0

    win_rate: float = 0.0

    gross_profit: float = 0.0

    gross_loss: float = 0.0

    net_profit: float = 0.0

    roi: float = 0.0

    profit_factor: float = 0.0

    expectancy: float = 0.0

    max_drawdown: float = 0.0

    sharpe_ratio: float = 0.0

    average_holding_minutes: float = 0.0

    average_win: float = 0.0

    average_loss: float = 0.0

    largest_win: float = 0.0

    largest_loss: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)

    notes: str = ""

    def calculate_metrics(self):

        if self.total_trades > 0:

            self.win_rate = round((self.winning_trades / self.total_trades) * 100, 2)

        self.net_profit = round(self.gross_profit - self.gross_loss, 2)

        self.final_balance = round(self.initial_balance + self.net_profit, 2)

        self.roi = round((self.net_profit / self.initial_balance) * 100, 2)

        if self.gross_loss > 0:

            self.profit_factor = round(self.gross_profit / self.gross_loss, 2)

    def to_dict(self):

        return {
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "gross_profit": self.gross_profit,
            "gross_loss": self.gross_loss,
            "net_profit": self.net_profit,
            "roi": self.roi,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "average_holding_minutes": self.average_holding_minutes,
            "average_win": self.average_win,
            "average_loss": self.average_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data):

        return cls(
            strategy_name=data.get("strategy_name", ""),
            strategy_version=data.get("strategy_version", 1),
            symbol=data.get("symbol", ""),
            timeframe=data.get("timeframe", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            initial_balance=data.get("initial_balance", 100000),
            final_balance=data.get("final_balance", 100000),
            total_trades=data.get("total_trades", 0),
            winning_trades=data.get("winning_trades", 0),
            losing_trades=data.get("losing_trades", 0),
            win_rate=data.get("win_rate", 0),
            gross_profit=data.get("gross_profit", 0),
            gross_loss=data.get("gross_loss", 0),
            net_profit=data.get("net_profit", 0),
            roi=data.get("roi", 0),
            profit_factor=data.get("profit_factor", 0),
            expectancy=data.get("expectancy", 0),
            max_drawdown=data.get("max_drawdown", 0),
            sharpe_ratio=data.get("sharpe_ratio", 0),
            average_holding_minutes=data.get("average_holding_minutes", 0),
            average_win=data.get("average_win", 0),
            average_loss=data.get("average_loss", 0),
            largest_win=data.get("largest_win", 0),
            largest_loss=data.get("largest_loss", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            notes=data.get("notes", ""),
        )
