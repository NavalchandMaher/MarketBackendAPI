from datetime import datetime
from db.mongodb import strategies

DEFAULT_STRATEGY = {
"strategy_name": "EMA_MACD_V1",
"version": 1,
"enabled": True,

# Signal Settings
"buy_threshold": 3,
"sell_threshold": -3,

# EMA Settings
"ema_fast": 20,
"ema_slow": 50,

# RSI Settings
"rsi_buy": 40,
"rsi_sell": 65,

# Market Filters
"adx_min": 25,
"volume_ratio_min": 1.3,

# Risk Management
"tp_percent": 2.0,
"sl_percent": 1.0,

# Learning Metrics
"win_rate": 0,
"profit_factor": 0,

"created_at": datetime.utcnow(),
"last_updated": datetime.utcnow()

}

class StrategyManager:
    @staticmethod
    def get_active_strategy():

        strategy = strategies.find_one({
            "enabled": True
        })

        if not strategy:

            strategies.insert_one(
                DEFAULT_STRATEGY
            )

            strategy = strategies.find_one({
                "enabled": True
            })

        return strategy

@staticmethod
def update_strategy(strategy_id, updates):

    updates["last_updated"] = (
        datetime.utcnow()
    )

    strategies.update_one(
        {"_id": strategy_id},
        {
            "$set": updates
        }
    )

@staticmethod
def create_new_version(
        old_strategy,
        updates):

    new_strategy = dict(old_strategy)

    new_strategy.pop("_id", None)

    new_strategy["version"] = (
        old_strategy["version"] + 1
    )

    new_strategy["enabled"] = True

    new_strategy["created_at"] = (
        datetime.utcnow()
    )

    new_strategy["last_updated"] = (
        datetime.utcnow()
    )

    new_strategy.update(updates)

    strategies.update_many(
        {},
        {
            "$set": {
                "enabled": False
            }
        }
    )

    strategies.insert_one(
        new_strategy
    )

    return new_strategy
def load_strategy():
    return (
        StrategyManager
        .get_active_strategy()
    )
