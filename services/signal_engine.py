import ta
from services.market_data import get_candles

def generate_signal(symbol):

    df = get_candles(symbol)

    df["ema20"] = ta.trend.EMAIndicator(
        df["close"],
        window=20
    ).ema_indicator()

    df["ema50"] = ta.trend.EMAIndicator(
        df["close"],
        window=50
    ).ema_indicator()

    df["rsi"] = ta.momentum.RSIIndicator(
        df["close"],
        window=14
    ).rsi()

    last = df.iloc[-1]

    if last["ema20"] > last["ema50"] and last["rsi"] > 55:
        return "BUY"

    if last["ema20"] < last["ema50"] and last["rsi"] < 45:
        return "SELL"

    return "HOLD"