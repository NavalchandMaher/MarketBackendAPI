"""
Performance Service
Market AI V2
"""

from datetime import datetime
from db.mongodb import closed_trades
from config import INITIAL_BALANCE


class PerformanceService:

    # ==========================================
    # LOAD CLOSED TRADES
    # ==========================================

    @staticmethod
    def trades(user_id=None):
        query = {}
        if user_id:
            query["user_id"] = user_id
        return list(closed_trades.find(query))

    # ==========================================
    # TOTAL TRADES
    # ==========================================

    @staticmethod
    def total_trades(user_id=None):
        query = {}
        if user_id:
            query["user_id"] = user_id
        return closed_trades.count_documents(query)

    # ==========================================
    # WIN COUNT
    # ==========================================

    @staticmethod
    def wins(user_id=None):
        query = {"result": "WIN"}
        if user_id:
            query["user_id"] = user_id
        return closed_trades.count_documents(query)

    # ==========================================
    # LOSS COUNT
    # ==========================================

    @staticmethod
    def losses(user_id=None):
        query = {"result": "LOSS"}
        if user_id:
            query["user_id"] = user_id
        return closed_trades.count_documents(query)

    # ==========================================
    # WIN RATE
    # ==========================================

    @staticmethod
    def win_rate(user_id=None):

        total = PerformanceService.total_trades(user_id=user_id)

        if total == 0:

            return 0

        wins = PerformanceService.wins(user_id=user_id)

        return round((wins / total) * 100, 2)

    # ==========================================
    # TOTAL PROFIT
    # ==========================================

    @staticmethod
    def total_profit(user_id=None):

        profit = 0

        for trade in PerformanceService.trades(user_id=user_id):

            pnl = trade.get("pnl", 0)

            if pnl > 0:

                profit += pnl

        return round(profit, 2)

    # ==========================================
    # TOTAL LOSS
    # ==========================================

    @staticmethod
    def total_loss(user_id=None):

        loss = 0

        for trade in PerformanceService.trades(user_id=user_id):

            pnl = trade.get("pnl", 0)

            if pnl < 0:

                loss += abs(pnl)

        return round(loss, 2)

    # ==========================================
    # NET PROFIT
    # ==========================================

    @staticmethod
    def net_profit(user_id=None):

        return round(
            PerformanceService.total_profit(user_id=user_id) - PerformanceService.total_loss(user_id=user_id), 2
        )

    # ==========================================
    # CURRENT BALANCE
    # ==========================================

    @staticmethod
    def current_balance(user_id=None):

        return round(INITIAL_BALANCE + PerformanceService.net_profit(user_id=user_id), 2)

        # ==========================================

    # PROFIT FACTOR
    # ==========================================

    @staticmethod
    def profit_factor(user_id=None):

        profit = PerformanceService.total_profit(user_id=user_id)

        loss = PerformanceService.total_loss(user_id=user_id)

        if loss == 0:

            return round(profit, 2)

        return round(profit / loss, 2)

    # ==========================================
    # AVERAGE WIN
    # ==========================================

    @staticmethod
    def average_win(user_id=None):

        wins = [
            trade["pnl"]
            for trade in PerformanceService.trades(user_id=user_id)
            if trade.get("pnl", 0) > 0
        ]

        if len(wins) == 0:

            return 0

        return round(sum(wins) / len(wins), 2)

    # ==========================================
    # AVERAGE LOSS
    # ==========================================

    @staticmethod
    def average_loss(user_id=None):

        losses = [
            abs(trade["pnl"])
            for trade in PerformanceService.trades(user_id=user_id)
            if trade.get("pnl", 0) < 0
        ]

        if len(losses) == 0:

            return 0

        return round(sum(losses) / len(losses), 2)

    # ==========================================
    # RISK / REWARD RATIO
    # ==========================================

    @staticmethod
    def risk_reward_ratio(user_id=None):

        avg_loss = PerformanceService.average_loss(user_id=user_id)

        if avg_loss == 0:

            return 0

        return round(PerformanceService.average_win(user_id=user_id) / avg_loss, 2)

    # ==========================================
    # MAX DRAWDOWN
    # ==========================================

    @staticmethod
    def max_drawdown(user_id=None):

        balance = INITIAL_BALANCE

        peak = balance

        max_dd = 0

        trades = sorted(
            PerformanceService.trades(user_id=user_id), key=lambda x: x.get("closed_at", datetime.min)
        )

        for trade in trades:

            balance += trade.get("pnl", 0)

            if balance > peak:

                peak = balance

            if peak > 0:

                drawdown = ((peak - balance) / peak) * 100

                if drawdown > max_dd:

                    max_dd = drawdown

        return round(max_dd, 2)

    # ==========================================
    # SHARPE RATIO
    # ==========================================

    @staticmethod
    def sharpe_ratio(risk_free_rate=0.0, user_id=None):

        pnls = [trade.get("pnl", 0) for trade in PerformanceService.trades(user_id=user_id)]

        if len(pnls) < 2:

            return 0

        avg_return = sum(pnls) / len(pnls)

        variance = sum((x - avg_return) ** 2 for x in pnls) / (len(pnls) - 1)

        std_dev = variance**0.5

        if std_dev == 0:

            return 0

        sharpe = (avg_return - risk_free_rate) / std_dev

        return round(sharpe, 2)
        # ==========================================

    # DAILY STATISTICS
    # ==========================================

    @staticmethod
    def daily_statistics(user_id=None):

        stats = {}

        for trade in PerformanceService.trades(user_id=user_id):

            closed_at = trade.get("closed_at")

            if not closed_at:

                continue

            day = closed_at.strftime("%Y-%m-%d")

            if day not in stats:

                stats[day] = {
                    "date": day,
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0,
                }

            stats[day]["total_trades"] += 1

            pnl = trade.get("pnl", 0)

            stats[day]["profit"] += pnl

            if pnl > 0:

                stats[day]["wins"] += 1

            else:

                stats[day]["losses"] += 1

        return sorted(stats.values(), key=lambda x: x["date"], reverse=True)

    # ==========================================
    # WEEKLY STATISTICS
    # ==========================================

    @staticmethod
    def weekly_statistics(user_id=None):

        stats = {}

        for trade in PerformanceService.trades(user_id=user_id):

            closed_at = trade.get("closed_at")

            if not closed_at:

                continue

            year, week, _ = closed_at.isocalendar()

            key = f"{year}-W{week}"

            if key not in stats:

                stats[key] = {
                    "week": key,
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0,
                }

            stats[key]["total_trades"] += 1

            pnl = trade.get("pnl", 0)

            stats[key]["profit"] += pnl

            if pnl > 0:

                stats[key]["wins"] += 1

            else:

                stats[key]["losses"] += 1

        return sorted(stats.values(), key=lambda x: x["week"], reverse=True)

    # ==========================================
    # MONTHLY STATISTICS
    # ==========================================

    @staticmethod
    def monthly_statistics(user_id=None):

        stats = {}

        for trade in PerformanceService.trades(user_id=user_id):

            closed_at = trade.get("closed_at")

            if not closed_at:

                continue

            key = closed_at.strftime("%Y-%m")

            if key not in stats:

                stats[key] = {
                    "month": key,
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0,
                }

            stats[key]["total_trades"] += 1

            pnl = trade.get("pnl", 0)

            stats[key]["profit"] += pnl

            if pnl > 0:

                stats[key]["wins"] += 1

            else:

                stats[key]["losses"] += 1

        return sorted(stats.values(), key=lambda x: x["month"], reverse=True)

    # ==========================================
    # SYMBOL PERFORMANCE
    # ==========================================

    @staticmethod
    def symbol_performance(user_id=None):

        performance = {}

        for trade in PerformanceService.trades(user_id=user_id):

            symbol = trade.get("symbol", "UNKNOWN")

            if symbol not in performance:

                performance[symbol] = {
                    "symbol": symbol,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0,
                }

            performance[symbol]["trades"] += 1

            pnl = trade.get("pnl", 0)

            performance[symbol]["profit"] += pnl

            if pnl > 0:

                performance[symbol]["wins"] += 1

            else:

                performance[symbol]["losses"] += 1

        return sorted(performance.values(), key=lambda x: x["profit"], reverse=True)

    # ==========================================
    # STRATEGY PERFORMANCE
    # ==========================================

    @staticmethod
    def strategy_performance(user_id=None):

        performance = {}

        for trade in PerformanceService.trades(user_id=user_id):

            strategy = trade.get("strategy_name", "DEFAULT")

            if strategy not in performance:

                performance[strategy] = {
                    "strategy": strategy,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit": 0,
                }

            performance[strategy]["trades"] += 1

            pnl = trade.get("pnl", 0)

            performance[strategy]["profit"] += pnl

            if pnl > 0:

                performance[strategy]["wins"] += 1

            else:

                performance[strategy]["losses"] += 1

        return sorted(performance.values(), key=lambda x: x["profit"], reverse=True)

        # ==========================================

    # EQUITY CURVE
    # ==========================================

    @staticmethod
    def equity_curve(user_id=None):

        balance = INITIAL_BALANCE

        curve = []

        trades = sorted(
            PerformanceService.trades(user_id=user_id), key=lambda x: x.get("closed_at", datetime.min)
        )

        for trade in trades:

            balance += trade.get("pnl", 0)

            curve.append(
                {
                    "trade_id": trade.get("trade_id"),
                    "date": trade.get("closed_at"),
                    "balance": round(balance, 2),
                }
            )

        return curve

    # ==========================================
    # ACCOUNT SUMMARY
    # ==========================================

    @staticmethod
    def account_summary(user_id=None):

        return {
            "initial_balance": INITIAL_BALANCE,
            "current_balance": PerformanceService.current_balance(user_id=user_id),
            "net_profit": PerformanceService.net_profit(user_id=user_id),
            "win_rate": PerformanceService.win_rate(user_id=user_id),
            "total_trades": PerformanceService.total_trades(user_id=user_id),
            "wins": PerformanceService.wins(user_id=user_id),
            "losses": PerformanceService.losses(user_id=user_id),
        }

    # ==========================================
    # PERFORMANCE SNAPSHOT
    # ==========================================

    @staticmethod
    def snapshot(user_id=None):

        return {
            "summary": PerformanceService.account_summary(user_id=user_id),
            "metrics": {
                "profit_factor": PerformanceService.profit_factor(user_id=user_id),
                "max_drawdown": PerformanceService.max_drawdown(user_id=user_id),
                "sharpe_ratio": PerformanceService.sharpe_ratio(user_id=user_id),
                "average_win": PerformanceService.average_win(user_id=user_id),
                "average_loss": PerformanceService.average_loss(user_id=user_id),
                "risk_reward": PerformanceService.risk_reward_ratio(user_id=user_id),
            },
        }

    # ==========================================
    # DASHBOARD
    # ==========================================

    @staticmethod
    def dashboard(user_id=None):

        return {
            "account": PerformanceService.account_summary(user_id=user_id),
            "snapshot": PerformanceService.snapshot(user_id=user_id),
            "daily": PerformanceService.daily_statistics(user_id=user_id),
            "weekly": PerformanceService.weekly_statistics(user_id=user_id),
            "monthly": PerformanceService.monthly_statistics(user_id=user_id),
            "symbols": PerformanceService.symbol_performance(user_id=user_id),
            "strategies": PerformanceService.strategy_performance(user_id=user_id),
            "equity_curve": PerformanceService.equity_curve(user_id=user_id),
        }

    # ==========================================
    # REFRESH
    # ==========================================

    @staticmethod
    def refresh(user_id=None):

        return PerformanceService.dashboard(user_id=user_id)

    # ==========================================
    # HEALTH CHECK
    # ==========================================

    @staticmethod
    def health(user_id=None):

        return {
            "service": "PerformanceService",
            "status": "UP",
            "timestamp": datetime.utcnow(),
            "closed_trades": PerformanceService.total_trades(user_id=user_id),
        }
