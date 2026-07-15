"""
Learning Engine
Market AI V2

This service analyzes every closed trade,
identifies why trades win or lose,
and continuously improves the trading strategy.
"""

from datetime import datetime

from db.mongodb import closed_trades, learning_logs, strategies, market_snapshots


class LearningEngine:

    # ==========================================================
    # LOAD CLOSED TRADES
    # ==========================================================

    @staticmethod
    def closed_trades(user_id=None):
        query = {}
        if user_id:
            query["user_id"] = user_id
        return list(closed_trades.find(query).sort("closed_at", -1))

    # ==========================================================
    # LOAD ACTIVE STRATEGY
    # ==========================================================

    @staticmethod
    def active_strategy(user_id=None):
        strategy = None

        if user_id:
            strategy = strategies.find_one(
                {"enabled": True, "user_id": user_id, "is_default": True}
            )
            if not strategy:
                strategy = strategies.find_one(
                    {"enabled": True, "user_id": user_id}
                )
        else:
            strategy = strategies.find_one(
                {"enabled": True, "is_default": True, "user_id": {"$exists": False}}
            )
            if not strategy:
                strategy = strategies.find_one({"enabled": True})

        if strategy:
            strategy["_id"] = str(strategy["_id"])

        return strategy

    # ==========================================================
    # LOAD STRATEGY BY VERSION
    # ==========================================================

    @staticmethod
    def strategy(version, user_id=None):
        query = {"version": version}
        if user_id:
            query["user_id"] = user_id
        strategy = strategies.find_one(query)

        if strategy:

            strategy["_id"] = str(strategy["_id"])

        return strategy

    # ==========================================================
    # LOAD SNAPSHOTS
    # ==========================================================

    @staticmethod
    def snapshots(limit=500):

        snapshots = []

        cursor = market_snapshots.find().sort("created_at", -1).limit(limit)

        for snapshot in cursor:

            snapshot["_id"] = str(snapshot["_id"])

            snapshots.append(snapshot)

        return snapshots

    # ==========================================================
    # SNAPSHOT BY TRADE
    # ==========================================================

    @staticmethod
    def snapshot(trade_id):

        snapshot = market_snapshots.find_one({"trade_id": trade_id})

        if snapshot:

            snapshot["_id"] = str(snapshot["_id"])

        return snapshot

    # ==========================================================
    # LOAD LEARNING LOGS
    # ==========================================================

    @staticmethod
    def logs(limit=100, user_id=None):
        logs = []
        query = {}
        if user_id:
            query["user_id"] = user_id
        cursor = learning_logs.find(query).sort("created_at", -1).limit(limit)

        for log in cursor:

            log["_id"] = str(log["_id"])

            logs.append(log)

        return logs

    # ==========================================================
    # SAVE LEARNING LOG
    # ==========================================================

    @staticmethod
    def save_log(title, details, strategy_version, user_id=None):
        log_doc = {
            "title": title,
            "details": details,
            "strategy_version": strategy_version,
            "created_at": datetime.utcnow(),
        }
        if user_id:
            log_doc["user_id"] = user_id
        learning_logs.insert_one(log_doc)

    # ==========================================================
    # TOTAL CLOSED TRADES
    # ==========================================================

    @staticmethod
    def total_closed_trades(user_id=None):
        query = {}
        if user_id:
            query["user_id"] = user_id
        return closed_trades.count_documents(query)

    # ==========================================================
    # WINNING TRADES
    # ==========================================================

    @staticmethod
    def winning_trades(user_id=None):
        query = {"result": "WIN"}
        if user_id:
            query["user_id"] = user_id
        return list(closed_trades.find(query))

    # ==========================================================
    # LOSING TRADES
    # ==========================================================

    @staticmethod
    def losing_trades(user_id=None):
        query = {"result": "LOSS"}
        if user_id:
            query["user_id"] = user_id
        return list(closed_trades.find(query))

    # ==========================================================
    # HEALTH
    # ==========================================================

    @staticmethod
    def health():

        return {
            "service": "LearningEngine",
            "status": "RUNNING",
            "closed_trades": LearningEngine.total_closed_trades(),
            "snapshots": market_snapshots.count_documents({}),
            "learning_logs": learning_logs.count_documents({}),
            "timestamp": datetime.utcnow(),
        }

        # ==========================================================

    # ANALYZE LOSING TRADES
    # ==========================================================

    @staticmethod
    def analyze_losses():

        losses = LearningEngine.losing_trades()

        report = {
            "total_losses": len(losses),
            "high_rsi": 0,
            "low_rsi": 0,
            "weak_adx": 0,
            "strong_adx": 0,
            "bullish_losses": 0,
            "bearish_losses": 0,
            "ranging_losses": 0,
            "trending_losses": 0,
        }

        for trade in losses:

            indicators = trade.get("indicators", {})

            rsi = indicators.get("rsi", 50)

            adx = indicators.get("adx", 20)

            regime = trade.get("market_regime", "UNKNOWN")

            signal = trade.get("signal", "WAIT")

            if rsi > 70:

                report["high_rsi"] += 1

            elif rsi < 30:

                report["low_rsi"] += 1

            if adx < 20:

                report["weak_adx"] += 1

            elif adx >= 25:

                report["strong_adx"] += 1

            if regime == "TRENDING":

                report["trending_losses"] += 1

            elif regime == "RANGING":

                report["ranging_losses"] += 1

            if signal == "BUY":

                report["bullish_losses"] += 1

            elif signal == "SELL":

                report["bearish_losses"] += 1

        return report

    # ==========================================================
    # ANALYZE WINNING TRADES
    # ==========================================================

    @staticmethod
    def analyze_wins():

        wins = LearningEngine.winning_trades()

        report = {
            "total_wins": len(wins),
            "high_rsi": 0,
            "low_rsi": 0,
            "weak_adx": 0,
            "strong_adx": 0,
            "bullish_wins": 0,
            "bearish_wins": 0,
            "ranging_wins": 0,
            "trending_wins": 0,
        }

        for trade in wins:

            indicators = trade.get("indicators", {})

            rsi = indicators.get("rsi", 50)

            adx = indicators.get("adx", 20)

            regime = trade.get("market_regime", "UNKNOWN")

            signal = trade.get("signal", "WAIT")

            if rsi > 70:

                report["high_rsi"] += 1

            elif rsi < 30:

                report["low_rsi"] += 1

            if adx < 20:

                report["weak_adx"] += 1

            elif adx >= 25:

                report["strong_adx"] += 1

            if regime == "TRENDING":

                report["trending_wins"] += 1

            elif regime == "RANGING":

                report["ranging_wins"] += 1

            if signal == "BUY":

                report["bullish_wins"] += 1

            elif signal == "SELL":

                report["bearish_wins"] += 1

        return report

    # ==========================================================
    # DETECT BAD INDICATORS
    # ==========================================================

    @staticmethod
    def detect_bad_indicators():

        losses = LearningEngine.analyze_losses()

        bad = []

        if losses["high_rsi"] > losses["total_losses"] * 0.40:

            bad.append("BUY at RSI > 70 is causing losses.")

        if losses["low_rsi"] > losses["total_losses"] * 0.40:

            bad.append("SELL at RSI < 30 is causing losses.")

        if losses["weak_adx"] > losses["total_losses"] * 0.50:

            bad.append("Low ADX trades should be filtered.")

        if losses["bullish_losses"] > losses["bearish_losses"]:

            bad.append("BUY strategy underperforming.")

        elif losses["bearish_losses"] > losses["bullish_losses"]:

            bad.append("SELL strategy underperforming.")

        return bad

    # ==========================================================
    # DETECT MARKET REGIME
    # ==========================================================

    @staticmethod
    def detect_market_regime():

        wins = LearningEngine.analyze_wins()

        losses = LearningEngine.analyze_losses()

        if wins["trending_wins"] > losses["trending_losses"]:

            return {
                "best_market": "TRENDING",
                "recommendation": "Prefer trend-following strategies.",
            }

        if wins["ranging_wins"] > losses["ranging_losses"]:

            return {
                "best_market": "RANGING",
                "recommendation": "Prefer range-bound strategies.",
            }

        return {
            "best_market": "UNKNOWN",
            "recommendation": "Collect more trade history.",
        }
        # ==========================================================

    # AUTO ADJUST BUY/SELL THRESHOLD
    # ==========================================================

    @staticmethod
    def adjust_thresholds(strategy):

        wins = LearningEngine.analyze_wins()
        losses = LearningEngine.analyze_losses()

        buy_threshold = strategy.get("buy_threshold", 3)
        sell_threshold = strategy.get("sell_threshold", -3)

        # Too many BUY losses -> make BUY stricter
        if losses["bullish_losses"] > wins["bullish_wins"]:

            buy_threshold = min(buy_threshold + 1, 8)

        # BUY performing well -> allow earlier entries
        elif wins["bullish_wins"] > losses["bullish_losses"] * 2:

            buy_threshold = max(buy_threshold - 1, 2)

        # Too many SELL losses
        if losses["bearish_losses"] > wins["bearish_wins"]:

            sell_threshold = max(sell_threshold - 1, -8)

        # SELL performing well
        elif wins["bearish_wins"] > losses["bearish_losses"] * 2:

            sell_threshold = min(sell_threshold + 1, -2)

        strategy["buy_threshold"] = buy_threshold
        strategy["sell_threshold"] = sell_threshold

        return strategy

    # ==========================================================
    # AUTO ADJUST TP / SL
    # ==========================================================

    @staticmethod
    def adjust_tp_sl(strategy):

        profit_factor = strategy.get("profit_factor", 1)

        tp = strategy.get("tp_percent", 2)
        sl = strategy.get("sl_percent", 1)

        if profit_factor > 2:

            tp += 0.5

        elif profit_factor < 1:

            tp = max(1, tp - 0.5)

        drawdown = strategy.get("drawdown", 0)

        if drawdown > 10:

            sl = max(0.5, sl - 0.25)

        strategy["tp_percent"] = round(tp, 2)
        strategy["sl_percent"] = round(sl, 2)

        return strategy

    # ==========================================================
    # AUTO ADJUST EMA
    # ==========================================================

    @staticmethod
    def adjust_ema(strategy):

        regime = LearningEngine.detect_market_regime()

        fast = strategy.get("ema_fast", 20)
        slow = strategy.get("ema_slow", 50)

        if regime["best_market"] == "TRENDING":

            fast = max(10, fast - 2)

            slow = max(30, slow - 5)

        elif regime["best_market"] == "RANGING":

            fast = min(30, fast + 2)

            slow = min(80, slow + 5)

        strategy["ema_fast"] = fast
        strategy["ema_slow"] = slow

        return strategy

    # ==========================================================
    # AUTO ADJUST RSI
    # ==========================================================

    @staticmethod
    def adjust_rsi(strategy):

        report = LearningEngine.analyze_losses()

        buy = strategy.get("rsi_buy", 40)
        sell = strategy.get("rsi_sell", 65)

        if report["high_rsi"] > report["total_losses"] * 0.30:

            sell = max(55, sell - 2)

        if report["low_rsi"] > report["total_losses"] * 0.30:

            buy = min(45, buy + 2)

        strategy["rsi_buy"] = buy
        strategy["rsi_sell"] = sell

        return strategy

    # ==========================================================
    # APPLY ALL OPTIMIZATIONS
    # ==========================================================

    @staticmethod
    def optimize_strategy(strategy):

        strategy = LearningEngine.adjust_thresholds(strategy)

        strategy = LearningEngine.adjust_tp_sl(strategy)

        strategy = LearningEngine.adjust_ema(strategy)

        strategy = LearningEngine.adjust_rsi(strategy)

        strategy["optimized_at"] = datetime.utcnow()

        return strategy

        # ==========================================================

    # SAVE NEW STRATEGY VERSION
    # ==========================================================

    @staticmethod
    def save_strategy(strategy):

        current = LearningEngine.active_strategy()

        if current:

            strategies.update_one(
                {
                    "_id": (
                        current["_id"]
                        if not isinstance(current["_id"], str)
                        else current.get("_object_id", current["_id"])
                    )
                },
                {"$set": {"enabled": False}},
            )

        strategy.pop("_id", None)

        strategy["version"] = strategy.get("version", 1) + 1

        strategy["enabled"] = True

        strategy["created_at"] = datetime.utcnow()

        # Preserve optional user scoping if present on the strategy dict
        strategies.insert_one(strategy)

        return strategy

    # ==========================================================
    # PERFORMANCE COMPARISON
    # ==========================================================

    @staticmethod
    def compare_performance():

        wins = len(LearningEngine.winning_trades())

        losses = len(LearningEngine.losing_trades())

        total = wins + losses

        if total == 0:

            return {"win_rate": 0, "status": "NO_DATA"}

        win_rate = round((wins / total) * 100, 2)

        if win_rate >= 70:

            status = "EXCELLENT"

        elif win_rate >= 60:

            status = "GOOD"

        elif win_rate >= 50:

            status = "AVERAGE"

        else:

            status = "POOR"

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "status": status,
        }

    # ==========================================================
    # WRITE LEARNING LOG
    # ==========================================================

    @staticmethod
    def write_learning_log(strategy):

        comparison = LearningEngine.compare_performance()

        log = {
            "strategy": strategy["strategy_name"],
            "version": strategy["version"],
            "buy_threshold": strategy["buy_threshold"],
            "sell_threshold": strategy["sell_threshold"],
            "ema_fast": strategy["ema_fast"],
            "ema_slow": strategy["ema_slow"],
            "rsi_buy": strategy["rsi_buy"],
            "rsi_sell": strategy["rsi_sell"],
            "tp_percent": strategy["tp_percent"],
            "sl_percent": strategy["sl_percent"],
            "performance": comparison,
            "created_at": datetime.utcnow(),
        }

        # If the strategy has a user_id, propagate it to the learning log
        if strategy.get("user_id"):
            log["user_id"] = strategy.get("user_id")
        learning_logs.insert_one(log)

    # ==========================================================
    # MAIN LEARNING METHOD
    # ==========================================================

    @staticmethod
    def learn():

        strategy = LearningEngine.active_strategy()

        if strategy is None:

            return {"success": False, "message": "No active strategy."}

        strategy = LearningEngine.optimize_strategy(strategy)

        strategy = LearningEngine.save_strategy(strategy)

        LearningEngine.write_learning_log(strategy)

        comparison = LearningEngine.compare_performance()

        return {
            "success": True,
            "message": "Learning completed successfully.",
            "strategy_version": strategy["version"],
            "performance": comparison,
        }

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    @staticmethod
    def dashboard():

        return {
            "performance": LearningEngine.compare_performance(),
            "market_regime": LearningEngine.detect_market_regime(),
            "bad_indicators": LearningEngine.detect_bad_indicators(),
            "learning_logs": LearningEngine.logs(20),
            "active_strategy": LearningEngine.active_strategy(),
        }
