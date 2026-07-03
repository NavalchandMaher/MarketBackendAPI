"""
Strategy Optimizer
Market AI V2

Compares all strategies and selects the best performer.
"""

from datetime import datetime

from db.mongodb import strategies, closed_trades, learning_logs


class StrategyOptimizer:

    # =====================================================
    # LOAD ALL STRATEGIES
    # =====================================================

    @staticmethod
    def all_strategies():

        result = []

        cursor = strategies.find().sort("version", -1)

        for strategy in cursor:

            strategy["_id"] = str(strategy["_id"])

            result.append(strategy)

        return result

    # =====================================================
    # LOAD ACTIVE STRATEGY
    # =====================================================

    @staticmethod
    def active_strategy():

        strategy = strategies.find_one({"enabled": True})

        if strategy:

            strategy["_id"] = str(strategy["_id"])

        return strategy

    # =====================================================
    # LOAD PERFORMANCE
    # =====================================================

    @staticmethod
    def performance(strategy_name):

        trades = list(closed_trades.find({"strategy_name": strategy_name}))

        total = len(trades)

        wins = 0
        losses = 0
        profit = 0

        for trade in trades:

            pnl = trade.get("pnl", 0)

            profit += pnl

            if pnl > 0:

                wins += 1

            else:

                losses += 1

        win_rate = 0

        if total > 0:

            win_rate = round((wins / total) * 100, 2)

        return {
            "strategy": strategy_name,
            "trades": total,
            "wins": wins,
            "losses": losses,
            "profit": round(profit, 2),
            "win_rate": win_rate,
        }

    # =====================================================
    # LOAD ALL PERFORMANCE
    # =====================================================

    @staticmethod
    def all_performance():

        report = []

        for strategy in StrategyOptimizer.all_strategies():

            report.append(StrategyOptimizer.performance(strategy["strategy_name"]))

        return report

    # =====================================================
    # COMPARE STRATEGIES
    # =====================================================

    @staticmethod
    def compare():

        comparison = []

        for strategy in StrategyOptimizer.all_strategies():

            perf = StrategyOptimizer.performance(strategy["strategy_name"])

            comparison.append(
                {
                    "strategy": strategy["strategy_name"],
                    "version": strategy.get("version", 1),
                    "enabled": strategy.get("enabled", False),
                    "profit": perf["profit"],
                    "win_rate": perf["win_rate"],
                    "wins": perf["wins"],
                    "losses": perf["losses"],
                    "trades": perf["trades"],
                }
            )

        comparison.sort(key=lambda x: (x["win_rate"], x["profit"]), reverse=True)

        return comparison

    # =====================================================
    # BEST STRATEGY
    # =====================================================

    @staticmethod
    def best_strategy():

        comparison = StrategyOptimizer.compare()

        if len(comparison) == 0:

            return None

        return comparison[0]

    # =====================================================
    # HEALTH
    # =====================================================

    @staticmethod
    def health():

        return {
            "service": "StrategyOptimizer",
            "strategies": strategies.count_documents({}),
            "active": strategies.count_documents({"enabled": True}),
            "closed_trades": closed_trades.count_documents({}),
            "timestamp": datetime.utcnow(),
        }
        # =====================================================

    # RANK STRATEGIES
    # =====================================================

    @staticmethod
    def rank_strategies():

        strategies_rank = StrategyOptimizer.compare()

        rank = 1

        for strategy in strategies_rank:

            strategy["rank"] = rank
            rank += 1

        return strategies_rank

    # =====================================================
    # DISABLE ALL STRATEGIES
    # =====================================================

    @staticmethod
    def disable_all():

        result = strategies.update_many(
            {}, {"$set": {"enabled": False, "updated_at": datetime.utcnow()}}
        )

        return result.modified_count

    # =====================================================
    # DISABLE BAD STRATEGIES
    # =====================================================

    @staticmethod
    def disable_bad_strategies(min_win_rate=50, min_trades=20):

        disabled = 0

        ranking = StrategyOptimizer.compare()

        for item in ranking:

            if item["trades"] >= min_trades and item["win_rate"] < min_win_rate:

                strategies.update_one(
                    {"strategy_name": item["strategy"]},
                    {
                        "$set": {
                            "enabled": False,
                            "disabled_reason": "Poor Performance",
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )

                disabled += 1

        return disabled

    # =====================================================
    # ENABLE BEST STRATEGY
    # =====================================================

    @staticmethod
    def enable_best_strategy():

        best = StrategyOptimizer.best_strategy()

        if best is None:

            return None

        StrategyOptimizer.disable_all()

        strategies.update_one(
            {"strategy_name": best["strategy"]},
            {"$set": {"enabled": True, "updated_at": datetime.utcnow()}},
        )

        learning_logs.insert_one(
            {
                "event": "BEST_STRATEGY_ENABLED",
                "strategy": best["strategy"],
                "version": best["version"],
                "win_rate": best["win_rate"],
                "profit": best["profit"],
                "created_at": datetime.utcnow(),
            }
        )

        return best

    # =====================================================
    # STRATEGY SCORE
    # =====================================================

    @staticmethod
    def strategy_score(strategy):

        score = 0

        score += strategy["win_rate"] * 2

        score += strategy["profit"] / 100

        score += strategy["wins"] * 3

        score -= strategy["losses"]

        return round(score, 2)

    # =====================================================
    # OPTIMIZE
    # =====================================================

    @staticmethod
    def optimize():

        ranking = StrategyOptimizer.rank_strategies()

        if len(ranking) == 0:

            return {"success": False, "message": "No strategies found."}

        StrategyOptimizer.disable_bad_strategies()

        best = StrategyOptimizer.enable_best_strategy()

        return {"success": True, "best_strategy": best, "ranking": ranking}
        # =====================================================

    # GENERATE OPTIMIZED STRATEGY
    # =====================================================

    @staticmethod
    def generate_strategy():

        best = StrategyOptimizer.best_strategy()

        if best is None:

            return None

        current = strategies.find_one({"strategy_name": best["strategy"]})

        if current is None:

            return None

        current.pop("_id", None)

        current["version"] = current.get("version", 1) + 1

        current["enabled"] = False

        current["created_at"] = datetime.utcnow()

        # -----------------------------
        # Small AI Optimizations
        # -----------------------------

        current["buy_threshold"] = min(current.get("buy_threshold", 3) + 1, 8)

        current["sell_threshold"] = max(current.get("sell_threshold", -3) - 1, -8)

        current["tp_percent"] = round(current.get("tp_percent", 2) * 1.05, 2)

        current["sl_percent"] = round(current.get("sl_percent", 1) * 0.95, 2)

        current["optimized"] = True

        current["optimized_at"] = datetime.utcnow()

        return current

    # =====================================================
    # SAVE NEW VERSION
    # =====================================================

    @staticmethod
    def save_new_version():

        strategy = StrategyOptimizer.generate_strategy()

        if strategy is None:

            return None

        result = strategies.insert_one(strategy)

        strategy["_id"] = str(result.inserted_id)

        learning_logs.insert_one(
            {
                "event": "NEW_STRATEGY_CREATED",
                "strategy": strategy["strategy_name"],
                "version": strategy["version"],
                "created_at": datetime.utcnow(),
            }
        )

        return strategy

    # =====================================================
    # DASHBOARD
    # =====================================================

    @staticmethod
    def dashboard():

        return {
            "best_strategy": StrategyOptimizer.best_strategy(),
            "ranking": StrategyOptimizer.rank_strategies(),
            "performance": StrategyOptimizer.all_performance(),
            "active_strategy": StrategyOptimizer.active_strategy(),
        }

    # =====================================================
    # RUN OPTIMIZER
    # =====================================================

    @staticmethod
    def run():

        ranking = StrategyOptimizer.rank_strategies()

        best = StrategyOptimizer.enable_best_strategy()

        new_version = StrategyOptimizer.save_new_version()

        return {
            "success": True,
            "best_strategy": best,
            "new_strategy": new_version,
            "ranking": ranking,
        }

    # =====================================================
    # STATUS
    # =====================================================

    @staticmethod
    def status():

        return {
            "service": "Strategy Optimizer",
            "strategies": strategies.count_documents({}),
            "active": strategies.count_documents({"enabled": True}),
            "timestamp": datetime.utcnow(),
        }
