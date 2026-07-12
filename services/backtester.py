"""
Backtester Engine
Market AI V2

Runs historical simulations on Binance data.
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from services.indicator_engine import calculate_all_indicators

from db.mongodb import (
    backtest_results,
    strategies
)

exchange = ccxt.binance({"options": {"defaultType": "future"}, "enableRateLimit": True})


class BackTester:

    # =====================================================
    # VALID TIMEFRAMES
    # =====================================================

    VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]

    # =====================================================
    # VALIDATE TIMEFRAME
    # =====================================================

    @staticmethod
    def validate_timeframe(tf):

        if tf in BackTester.VALID_TIMEFRAMES:

            return tf

        return "5m"

    # =====================================================
    # LOAD HISTORICAL DATA
    # =====================================================

    @staticmethod
    def load_history(symbol="BTCUSDT", timeframe="5m", days=365):

        timeframe = BackTester.validate_timeframe(timeframe)

        pair = symbol.replace("USDT", "/USDT")

        since = exchange.parse8601(
            (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        )

        candles = []

        while True:

            batch = exchange.fetch_ohlcv(
                pair, timeframe=timeframe, since=since, limit=1000
            )

            if not batch:

                break

            candles.extend(batch)

            since = batch[-1][0] + 1

            if len(batch) < 1000:

                break

        df = pd.DataFrame(
            candles, columns=["time", "open", "high", "low", "close", "volume"]
        )

        df["datetime"] = pd.to_datetime(df["time"], unit="ms")

        return df

    # =====================================================
    # PREPARE INDICATORS
    # =====================================================

    @staticmethod
    def prepare(df):

        df, summary = calculate_all_indicators(df)

        return df

    # =====================================================
    # REPLAY CANDLES
    # =====================================================

    @staticmethod
    def replay(df):

        for index in range(250, len(df)):

            history = df.iloc[:index].copy()

            yield history

    # =====================================================
    # CURRENT CANDLE
    # =====================================================

    @staticmethod
    def current(history):

        return history.iloc[-1]

    # =====================================================
    # PREVIOUS CANDLE
    # =====================================================

    @staticmethod
    def previous(history):

        return history.iloc[-2]

    # =====================================================
    # MARKET SNAPSHOT
    # =====================================================

    @staticmethod
    def snapshot(history):

        last = history.iloc[-1]

        return {
            "time": str(last["datetime"]),
            "price": float(last["close"]),
            "volume": float(last["volume"]),
            "ema20": float(last["ema20"]),
            "ema50": float(last["ema50"]),
            "rsi": float(last["rsi"]),
            "macd": float(last["macd"]),
            "adx": float(last["adx"]),
            "atr": float(last["atr"]),
        }

    # =====================================================
    # HEALTH
    # =====================================================

    @staticmethod
    def health():

        return {
            "service": "BackTester",
            "exchange": "Binance Futures",
            "status": "READY",
        }
        # =====================================================

    # EXECUTE STRATEGY
    # =====================================================

    @staticmethod
    def execute_strategy(history, strategy):
        try:
            candle = history.iloc[-1]

            score = 0

            # EMA
            if candle.get("ema20", 0) > candle.get("ema50", 0):
                score += 2
            else:
                score -= 2

            # RSI
            rsi_buy = strategy.get("rsi_buy", 35)
            rsi_sell = strategy.get("rsi_sell", 70)

            if candle.get("rsi", 0) < rsi_buy:
                score += 2
            elif candle.get("rsi", 0) > rsi_sell:
                score -= 2

            # MACD
            if candle.get("macd", 0) > candle.get("macd_signal", 0):
                score += 1
            else:
                score -= 1

            # ADX
            if candle.get("adx", 0) > 25:
                score += 1

            # SuperTrend
            if candle.get("supertrend_direction", "BULLISH") == "BULLISH":
                score += 1
            else:
                score -= 1

            buy_threshold = strategy.get("buy_threshold", 3)
            sell_threshold = strategy.get("sell_threshold", -3)

            if score >= buy_threshold:
                return "BUY"

            if score <= sell_threshold:
                return "SELL"
        except Exception:
            # If indicator data is missing or malformed, skip this step
            return "WAIT"

        return "WAIT"

    # =====================================================
    # CREATE VIRTUAL TRADE
    # =====================================================

    @staticmethod
    def open_virtual_trade(signal, candle, strategy):

        entry = float(candle["close"])

        tp_percent = strategy.get("tp_percent", 2)

        sl_percent = strategy.get("sl_percent", 1)

        if signal == "BUY":

            tp = entry * (1 + tp_percent / 100)

            sl = entry * (1 - sl_percent / 100)

        else:

            tp = entry * (1 - tp_percent / 100)

            sl = entry * (1 + sl_percent / 100)

        return {
            "signal": signal,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "entry_time": candle["datetime"],
            "status": "OPEN",
        }

    # =====================================================
    # TP / SL CHECK
    # =====================================================

    @staticmethod
    def check_trade(trade, candle):

        high = candle["high"]

        low = candle["low"]

        if trade["signal"] == "BUY":

            if high >= trade["tp"]:

                trade["status"] = "WIN"

                trade["exit"] = trade["tp"]

                trade["exit_time"] = candle["datetime"]

                trade["pnl"] = trade["tp"] - trade["entry"]

                return trade

            if low <= trade["sl"]:

                trade["status"] = "LOSS"

                trade["exit"] = trade["sl"]

                trade["exit_time"] = candle["datetime"]

                trade["pnl"] = trade["sl"] - trade["entry"]

                return trade

        else:

            if low <= trade["tp"]:

                trade["status"] = "WIN"

                trade["exit"] = trade["tp"]

                trade["exit_time"] = candle["datetime"]

                trade["pnl"] = trade["entry"] - trade["tp"]

                return trade

            if high >= trade["sl"]:

                trade["status"] = "LOSS"

                trade["exit"] = trade["sl"]

                trade["exit_time"] = candle["datetime"]

                trade["pnl"] = trade["entry"] - trade["sl"]

                return trade

        return trade

    # =====================================================
    # RUN SINGLE STRATEGY
    # =====================================================

    @staticmethod
    def run_strategy(df, strategy):

        trades = []

        current_trade = None

        replay = BackTester.replay(df)

        for history in replay:

            candle = history.iloc[-1]

            if current_trade is None:

                signal = BackTester.execute_strategy(history, strategy)

                if signal != "WAIT":

                    current_trade = BackTester.open_virtual_trade(
                        signal, candle, strategy
                    )

            else:

                current_trade = BackTester.check_trade(current_trade, candle)

                if current_trade["status"] != "OPEN":

                    trades.append(current_trade)

                    current_trade = None

        return trades
        # =====================================================

    # CALCULATE PERFORMANCE
    # =====================================================

    @staticmethod
    def performance(trades):

        total = len(trades)

        wins = len([t for t in trades if t["status"] == "WIN"])

        losses = len([t for t in trades if t["status"] == "LOSS"])

        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)

        gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))

        net_profit = gross_profit - gross_loss

        win_rate = round((wins / total) * 100, 2) if total else 0

        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "net_profit": round(net_profit, 2),
            "profit_factor": profit_factor,
        }

    # =====================================================
    # MAX DRAWDOWN
    # =====================================================

    @staticmethod
    def max_drawdown(trades):

        equity = 10000

        peak = equity

        max_dd = 0

        for trade in trades:

            equity += trade["pnl"]

            if equity > peak:

                peak = equity

            drawdown = peak - equity

            if drawdown > max_dd:

                max_dd = drawdown

        return round(max_dd, 2)

    # =====================================================
    # SHARPE RATIO
    # =====================================================

    @staticmethod
    def sharpe_ratio(trades):

        if len(trades) < 2:

            return 0

        returns = [trade["pnl"] for trade in trades]

        average = sum(returns) / len(returns)

        variance = sum((x - average) ** 2 for x in returns) / (len(returns) - 1)

        std = variance**0.5

        if std == 0:

            return 0

        return round(average / std, 2)

    # =====================================================
    # EXPECTANCY
    # =====================================================

    @staticmethod
    def expectancy(trades):

        wins = [t["pnl"] for t in trades if t["pnl"] > 0]

        losses = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]

        if len(trades) == 0:

            return 0

        win_rate = len(wins) / len(trades)

        loss_rate = len(losses) / len(trades)

        avg_win = sum(wins) / len(wins) if wins else 0

        avg_loss = sum(losses) / len(losses) if losses else 0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        return round(expectancy, 2)

    # =====================================================
    # PERFORMANCE REPORT
    # =====================================================

    @staticmethod
    def report(trades):

        perf = BackTester.performance(trades)

        perf["drawdown"] = BackTester.max_drawdown(trades)

        perf["sharpe_ratio"] = BackTester.sharpe_ratio(trades)

        perf["expectancy"] = BackTester.expectancy(trades)

        return perf

    from db.mongodb import backtest_results, strategies

    # =====================================================
    # RUN ALL STRATEGIES
    # =====================================================

    @staticmethod
    def run_all(symbol="BTCUSDT", timeframe="5m", days=365):

        df = BackTester.load_history(symbol, timeframe, days)

        df = BackTester.prepare(df)

        results = []

        strategy_list = list(strategies.find({"enabled": True}))

        if len(strategy_list) == 0:

            strategy_list = list(strategies.find())

        for strategy in strategy_list:

            trades = BackTester.run_strategy(df, strategy)

            report = BackTester.report(trades)

            report["strategy_name"] = strategy.get(
                "strategy_name", strategy.get("name", "UNKNOWN")
            )

            report["strategy_version"] = strategy.get("version", 1)

            report["symbol"] = symbol

            report["timeframe"] = timeframe

            report["days"] = days

            results.append(report)

        return results

    # =====================================================
    # BEST STRATEGY
    # =====================================================

    @staticmethod
    def best_strategy(results):

        if not results:

            return None

        return sorted(
            results,
            key=lambda x: (x["win_rate"], x["profit_factor"], x["net_profit"]),
            reverse=True,
        )[0]

    # =====================================================
    # SAVE REPORT
    # =====================================================

    @staticmethod
    def save_report(report):

        report["created_at"] = datetime.utcnow()

        result = backtest_results.insert_one(report)

        report["_id"] = str(result.inserted_id)

        return report

    # =====================================================
    # SAVE ALL REPORTS
    # =====================================================

    @staticmethod
    def save_all(results):

        saved = []

        for report in results:

            saved.append(BackTester.save_report(report))

        return saved

    # =====================================================
    # DASHBOARD
    # =====================================================

    @staticmethod
    def dashboard(symbol="BTCUSDT", timeframe="5m", days=365):

        reports = BackTester.run_all(symbol, timeframe, days)

        best = BackTester.best_strategy(reports)

        BackTester.save_all(reports)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "backtest_days": days,
            "total_strategies": len(reports),
            "best_strategy": best,
            "all_results": reports,
        }

    # =====================================================
    # RUN COMPLETE BACKTEST
    # =====================================================

    @staticmethod
    def run(symbol="BTCUSDT", timeframe="5m", days=365):

        dashboard = BackTester.dashboard(symbol, timeframe, days)

        return {
            "success": True,
            "message": "Backtest completed successfully.",
            "dashboard": dashboard,
        }

    # =====================================================
    # HEALTH
    # =====================================================

    @staticmethod
    def health():

        return {
            "service": "BackTester",
            "status": "READY",
            "stored_reports": backtest_results.count_documents({}),
            "timestamp": datetime.utcnow(),
        }
