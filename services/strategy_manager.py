from db.mongodb import strategies

DEFAULT_STRATEGY = {
    "strategy_name": "EMA_MACD_V1",
    "version": 1,
    "enabled": True,
    "buy_threshold": 3,
    "sell_threshold": -3,
    "ema_fast": 20,
    "ema_slow": 50,
    "rsi_buy": 40,
    "rsi_sell": 65,
    "adx_min": 25,
    "volume_ratio_min": 1.3
}

class StrategyManager:

    @staticmethod
    def get_active_strategy():

        strategy = strategies.find_one({"enabled": True})

        if not strategy:
            strategies.insert_one(DEFAULT_STRATEGY)
            strategy = strategies.find_one({"enabled": True})

        return strategy