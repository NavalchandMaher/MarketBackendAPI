"""
Backtester Engine
Market AI V2

Runs historical simulations on Binance data.
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
from services.indicator_engine import calculate_all_indicators, ema, rsi

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
    def _prepare_history_for_strategy(history):
        history = history.copy()

        if len(history) < 2:
            return history

        if "rsi" not in history.columns or "macd" not in history.columns:
            history = BackTester.prepare(history)

        return history

    @staticmethod
    def _evaluate_condition(condition, history):
        if not isinstance(condition, dict):
            return False

        if not condition.get("enabled", True):
            return False

        indicator = condition.get("indicator") or condition
        if not isinstance(indicator, dict):
            return False

        indicator_id = str(indicator.get("id", "")).lower()
        params = indicator.get("parameter") or indicator.get("parameters") or {}
        if not isinstance(params, dict):
            params = {}

        candle = history.iloc[-1]
        previous = history.iloc[-2] if len(history) > 1 else candle

        if indicator_id == "ema":
            fast_period = int(params.get("fast", 20) or 20)
            slow_period = int(params.get("slow", 50) or 50)
            history["ema_fast"] = ema(history, fast_period)
            history["ema_slow"] = ema(history, slow_period)
            candle = history.iloc[-1]
            previous = history.iloc[-2] if len(history) > 1 else candle
            current_fast = float(candle.get("ema_fast", 0))
            current_slow = float(candle.get("ema_slow", 0))
            prev_fast = float(previous.get("ema_fast", current_fast))
            prev_slow = float(previous.get("ema_slow", current_slow))
            condition_name = str(params.get("condition", "Bullish Cross")).lower()

            if condition_name in {"bullish cross", "cross above"}:
                return current_fast > current_slow and (prev_fast <= prev_slow or current_fast >= prev_fast)
            if condition_name in {"bearish cross", "cross below"}:
                return current_fast < current_slow and (prev_fast >= prev_slow or current_fast <= prev_fast)
            if condition_name in {"above"}:
                return current_fast > current_slow
            if condition_name in {"below"}:
                return current_fast < current_slow
            return current_fast > current_slow

        if indicator_id == "rsi":
            period = int(params.get("length", params.get("period", 14)) or 14)
            if "rsi" not in history.columns:
                history["rsi"] = rsi(history, period)
            candle = history.iloc[-1]
            previous = history.iloc[-2] if len(history) > 1 else candle
            value = float(candle.get("rsi", 0))
            prev_value = float(previous.get("rsi", value))
            threshold = float(params.get("value", params.get("overbought", 50)) or 50)
            condition_name = str(params.get("condition", "Greater Than")).lower()

            if condition_name == "greater than":
                return value > threshold
            if condition_name == "less than":
                return value < threshold
            if condition_name == "cross above":
                return value > threshold and prev_value <= threshold
            if condition_name == "cross below":
                return value < threshold and prev_value >= threshold
            if condition_name == "overbought":
                return value > float(params.get("overbought", 70) or 70)
            if condition_name == "oversold":
                return value < float(params.get("oversold", 30) or 30)
            return value < float(params.get("oversold", 30) or 30)

        if indicator_id == "macd":
            if "macd" not in history.columns or "macd_signal" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            current_macd = float(candle.get("macd", 0))
            current_signal = float(candle.get("macd_signal", 0))
            condition_name = str(params.get("condition", "Bullish Cross")).lower()
            if condition_name in {"bullish cross", "macd above signal"}:
                return current_macd > current_signal
            if condition_name in {"bearish cross", "macd below signal"}:
                return current_macd < current_signal
            if condition_name == "histogram > 0":
                return float(candle.get("macd_histogram", 0)) > 0
            if condition_name == "histogram < 0":
                return float(candle.get("macd_histogram", 0)) < 0
            return current_macd > current_signal

        if indicator_id == "supertrend":
            if "supertrend_direction" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            direction = str(candle.get("supertrend_direction", "BULLISH")).upper()
            current_price = float(candle.get("close", 0))
            current_supertrend = float(candle.get("supertrend", 0))
            condition_name = str(params.get("condition", "Trend Up")).lower()
            if condition_name in {"trend up", "trend change"}:
                return direction == "BULLISH"
            if condition_name in {"trend down"}:
                return direction == "BEARISH"
            if condition_name in {"price above supertrend"}:
                return current_price > current_supertrend
            if condition_name in {"price below supertrend"}:
                return current_price < current_supertrend
            return direction == "BULLISH"

        if indicator_id == "vwap":
            if "vwap" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            current_price = float(candle.get("close", 0))
            current_vwap = float(candle.get("vwap", 0))
            condition_name = str(params.get("condition", "Above VWAP")).lower()
            if condition_name in {"above vwap"}:
                return current_price > current_vwap
            if condition_name in {"below vwap"}:
                return current_price < current_vwap
            if condition_name in {"cross above"}:
                return current_price > current_vwap and float(previous.get("close", 0)) <= float(previous.get("vwap", 0))
            if condition_name in {"cross below"}:
                return current_price < current_vwap and float(previous.get("close", 0)) >= float(previous.get("vwap", 0))
            return current_price > current_vwap

        if indicator_id == "adx":
            if "adx" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            adx_value = float(candle.get("adx", 0))
            condition_name = str(params.get("condition", "ADX >")).lower()
            if condition_name in {"adx >"}:
                return adx_value > float(params.get("value", 25) or 25)
            if condition_name in {"adx <"}:
                return adx_value < float(params.get("value", 25) or 25)
            if condition_name in {"strong trend"}:
                return adx_value >= 25
            if condition_name in {"weak trend"}:
                return adx_value < 25
            return adx_value > float(params.get("value", 25) or 25)

        if indicator_id == "bollinger":
            if "bb_upper" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            upper = float(candle.get("bb_upper", 0))
            lower = float(candle.get("bb_lower", 0))
            current_price = float(candle.get("close", 0))
            condition_name = str(params.get("condition", "Upper Breakout")).lower()
            if condition_name in {"upper breakout", "price above upper"}:
                return current_price > upper
            if condition_name in {"lower breakout", "price below lower"}:
                return current_price < lower
            return current_price > upper

        if indicator_id == "atr":
            if "atr" not in history.columns:
                history = BackTester.prepare(history)
            candle = history.iloc[-1]
            atr_value = float(candle.get("atr", 0))
            condition_name = str(params.get("condition", "ATR >")).lower()
            if condition_name == "atr >":
                return atr_value > float(params.get("value", 2.0) or 2.0)
            if condition_name == "atr <":
                return atr_value < float(params.get("value", 2.0) or 2.0)
            if condition_name in {"atr increasing", "atr rising"}:
                return atr_value > float(previous.get("atr", atr_value))
            if condition_name in {"atr decreasing", "atr falling"}:
                return atr_value < float(previous.get("atr", atr_value))
            return atr_value > float(params.get("value", 2.0) or 2.0)

        return False

    @staticmethod
    def execute_strategy(history, strategy):
        try:
            history = BackTester._prepare_history_for_strategy(history)

            buy_conditions = strategy.get("buy_conditions") or []
            sell_conditions = strategy.get("sell_conditions") or []
            if not buy_conditions and not sell_conditions:
                indicator_params = strategy.get("indicator_parameters") or {}
                if isinstance(indicator_params, dict):
                    buy_conditions = indicator_params.get("buy_conditions") or []
                    sell_conditions = indicator_params.get("sell_conditions") or []

            if buy_conditions:
                if all(BackTester._evaluate_condition(condition, history) for condition in buy_conditions if condition.get("enabled", True)):
                    return "BUY"

            if sell_conditions:
                if all(BackTester._evaluate_condition(condition, history) for condition in sell_conditions if condition.get("enabled", True)):
                    return "SELL"

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

        # Preserve any provided user scoping; if not present, explicitly set to None
        if "user_id" not in report:
            report["user_id"] = None

        result = backtest_results.insert_one(report)

        report["_id"] = str(result.inserted_id)

        return report

    # =====================================================
    # SAVE ALL REPORTS
    # =====================================================

    @staticmethod
    def save_all(results, user_id: str | None = None):

        saved = []

        for report in results:

            if user_id:
                report["user_id"] = user_id

            saved.append(BackTester.save_report(report))

        return saved

    # =====================================================
    # DASHBOARD
    # =====================================================

    @staticmethod

    def dashboard(symbol="BTCUSDT", timeframe="5m", days=365, user_id: str | None = None):

        reports = BackTester.run_all(symbol, timeframe, days)

        best = BackTester.best_strategy(reports)

        # Save reports; attach user_id when provided
        BackTester.save_all(reports, user_id=user_id)

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
    def run(symbol="BTCUSDT", timeframe="5m", days=365, user_id: str | None = None):

        dashboard = BackTester.dashboard(symbol, timeframe, days, user_id=user_id)

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
