import ccxt
import pandas as pd

from db.mongodb import backtest_results
from services.strategy_manager import load_strategy

exchange = ccxt.binance({
    "options": {
        "defaultType": "future"
    }
})


def run_backtest(symbol="BTCUSDT"):

    strategy = load_strategy()

    pair = symbol.replace("USDT", "/USDT")

    candles = exchange.fetch_ohlcv(
        pair,
        timeframe="1h",
        limit=5000
    )

    df = pd.DataFrame(
        candles,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["ema20"] = (
        df["close"]
        .ewm(span=20)
        .mean()
    )

    df["ema50"] = (
        df["close"]
        .ewm(span=50)
        .mean()
    )

    wins = 0
    losses = 0
    trades = 0
    total_profit = 0

    tp_percent = strategy["tp_percent"]
    sl_percent = strategy["sl_percent"]

    for i in range(100, len(df) - 10):

        row = df.iloc[i]

        price = row["close"]

        signal = None

        if row["ema20"] > row["ema50"]:
            signal = "BUY"

        elif row["ema20"] < row["ema50"]:
            signal = "SELL"

        if signal is None:
            continue

        trades += 1

        future = df.iloc[i + 1:i + 10]

        if signal == "BUY":

            tp = price * (
                1 + tp_percent / 100
            )

            sl = price * (
                1 - sl_percent / 100
            )

            result = None

            for _, candle in future.iterrows():

                if candle["high"] >= tp:
                    result = "WIN"
                    break

                if candle["low"] <= sl:
                    result = "LOSS"
                    break

        else:

            tp = price * (
                1 - tp_percent / 100
            )

            sl = price * (
                1 + sl_percent / 100
            )

            result = None

            for _, candle in future.iterrows():

                if candle["low"] <= tp:
                    result = "WIN"
                    break

                if candle["high"] >= sl:
                    result = "LOSS"
                    break

        if result == "WIN":
            wins += 1
            total_profit += tp_percent

        else:
            losses += 1
            total_profit -= sl_percent

    win_rate = (
        round(
            wins * 100 / trades,
            2
        )
        if trades
        else 0
    )

    result = {
        "symbol": symbol,
        "strategy": strategy["name"],
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "net_profit_percent": round(
            total_profit,
            2
        )
    }

    backtest_results.insert_one(result)

    return result