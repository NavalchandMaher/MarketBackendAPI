import ccxt
import pandas as pd

exchange = ccxt.binance({
    "options": {
        "defaultType": "future"
    }
})

class MarketData:

    @staticmethod
    def get_ohlcv(symbol, timeframe, limit=250):

        pair = symbol.replace("USDT", "/USDT")

        bars = exchange.fetch_ohlcv(
            pair,
            timeframe=timeframe,
            limit=limit
        )

        return pd.DataFrame(
            bars,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )