import ccxt
import pandas as pd
import ta
import requests
from services.strategy_manager import StrategyManager
from services.paper_trading import PaperTrading
from db.mongodb import paper_trades

exchange = ccxt.binance({
    "options": {
        "defaultType": "future"
    }
})

LAST_OI = {}
LAST_PRICE = {}

VALID_TF = [
    "1m", "3m", "5m",
    "15m", "30m",
    "1h", "2h", "4h", "1d"
]


def safe(v, d=0):
    try:
        if pd.isna(v):
            return d
        return float(v)
    except:
        return d


def validate_tf(tf):
    return tf if tf in VALID_TF else "5m"


def get_pcr(symbol):
    try:
        currency = "BTC" if "BTC" in symbol else "ETH"

        url = (
            "https://www.deribit.com/api/v2/public/"
            f"get_book_summary_by_currency?currency={currency}&kind=option"
        )

        data = requests.get(url, timeout=5).json()["result"]

        call = 0
        put = 0

        for item in data:

            oi = float(item["open_interest"])

            if item["instrument_name"].endswith("C"):
                call += oi
            else:
                put += oi

        return put / call if call else 1

    except:
        return 1


def get_oi(symbol, price):

    try:
        data = exchange.fetch_open_interest(symbol)

        current = safe(data.get("openInterest", 0))

        prev_oi = LAST_OI.get(symbol, current)
        prev_price = LAST_PRICE.get(symbol, price)

        LAST_OI[symbol] = current
        LAST_PRICE[symbol] = price

        oi_change = (
            ((current - prev_oi) / current) * 100
            if current else 0
        )

        return current, oi_change, prev_price

    except:
        return 0, 0, price


def analyze_market(symbol="BTCUSDT", timeframe="5m"):

    timeframe = validate_tf(timeframe)

    pair = symbol.replace("USDT", "/USDT")

    # MAIN TF

    bars = exchange.fetch_ohlcv(
        pair,
        timeframe=timeframe,
        limit=250
    )

    df = pd.DataFrame(
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

    if len(df) < 100:
        return {
            "error": "Not enough data"
        }

    # HIGHER TF

    try:

        bars_htf = exchange.fetch_ohlcv(
            pair,
            timeframe="1h",
            limit=200
        )

        df_htf = pd.DataFrame(
            bars_htf,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        df_htf["ema50"] = (
            df_htf["close"]
            .ewm(span=50)
            .mean()
        )

        htf_trend = (
            "BULLISH"
            if df_htf.iloc[-2]["close"]
               > df_htf.iloc[-2]["ema50"]
            else "BEARISH"
        )

    except:
        htf_trend = "NEUTRAL"

    # INDICATORS

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

    df["rsi"] = (
        ta.momentum
        .RSIIndicator(df["close"])
        .rsi()
    )

    macd = ta.trend.MACD(df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    adx_ind = ta.trend.ADXIndicator(
        df["high"],
        df["low"],
        df["close"]
    )

    df["adx"] = adx_ind.adx()

    bb = ta.volatility.BollingerBands(
        df["close"]
    )

    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    candle = df.iloc[-2]

    price = safe(candle["close"])
    ema20 = safe(candle["ema20"])
    ema50 = safe(candle["ema50"])
    rsi = safe(candle["rsi"])
    macd_val = safe(candle["macd"])
    macd_sig = safe(candle["macd_signal"])
    adx = safe(candle["adx"])
    bb_high = safe(candle["bb_high"])
    bb_low = safe(candle["bb_low"])

    vol_avg = safe(
        df["volume"]
        .rolling(20)
        .mean()
        .iloc[-2],
        1
    )

    volume_ratio = (
        safe(candle["volume"]) / vol_avg
        if vol_avg else 1
    )

    pcr = get_pcr(symbol)

    futures_oi, oi_change, prev_price = (
        get_oi(pair, price)
    )

   # LOAD STRATEGY

    strategy = StrategyManager.get_active_strategy()

    BUY_THRESHOLD = strategy.get("buy_threshold", 3)
    SELL_THRESHOLD = strategy.get("sell_threshold", -3)
    TP_PERCENT = strategy.get("tp_percent", 2)
    SL_PERCENT = strategy.get("sl_percent", 1)

    score = 0
    max_score = 12

    # EMA
    score += 2 if ema20 > ema50 else -2

    # RSI
    if rsi < 30:
        score += 2
    elif rsi < 40:
        score += 1
    elif rsi > 70:
        score -= 2
    elif rsi > 60:
        score -= 1

    # MACD
    score += 1 if macd_val > macd_sig else -1

    # BB
    if price < bb_low:
        score += 1

    if price > bb_high:
        score -= 1

    # OI
    if price > prev_price and oi_change > 1:
        score += 2
    elif price < prev_price and oi_change > 1:
        score -= 2

    # PCR
    if pcr > 1.2:
        score += 1
    elif pcr < 0.8:
        score -= 1

    # Volume
    if volume_ratio > 1.3:
        score += 1

    # HTF
    if htf_trend == "BULLISH":
        score += 1
    elif htf_trend == "BEARISH":
        score -= 1
    

    # REGIME

    regime = (
    "TRENDING"
    if adx > 25
    else "RANGING"
    )

    # EXTRA SCORING

    if adx > 25:
        score += 1

    if volume_ratio > 1.5:
        score += 1

    if macd_val > macd_sig and rsi > 50:
        score += 1

    if ema20 > ema50 and htf_trend == "BULLISH":
        score += 1

    # SIGNAL

    if score >= BUY_THRESHOLD:
        signal = "BUY"

    elif score <= SELL_THRESHOLD:
        signal = "SELL"

    else:
        signal = "WAIT"

    confidence = min(
    95,
    int((abs(score) / max_score) * 100)
    )

    # SNAPSHOT FOR LEARNING ENGINE

    snapshot = {
    "ema20": round(ema20, 2),
    "ema50": round(ema50, 2),
    "rsi": round(rsi, 2),
    "macd": round(macd_val, 3),
    "adx": round(adx, 2),
    "pcr": round(pcr, 2),
    "volume_ratio": round(volume_ratio, 2),
    "oi_change_pct": round(oi_change, 2),
    "score": score,
    "market_regime": regime,
    "htf_trend": htf_trend
    }

    # PREVENT DUPLICATE OPEN TRADES

    existing_trade = paper_trades.find_one({
    "symbol": symbol,
    "status": "OPEN"
    })
    if not existing_trade:
        PaperTrading.open_trade({
            "symbol": symbol,
            "timeframe": timeframe,
            "strategy_name":
                strategy["strategy_name"],
            "strategy_version":
                strategy["version"],
            "signal": signal,
            "price": price,
            "confidence": confidence,
            "market_regime": regime,

            "indicators": {
                "ema20": ema20,
                "ema50": ema50,
                "rsi": rsi,
                "macd": macd_val,
                "adx": adx,
                "pcr": pcr,
                "volume_ratio": volume_ratio,
                "oi_change_pct": oi_change
            }
        })
    # CHART

    chart = (
    df.tail(100)[
    [
    "time",
    "close",
    "ema20",
    "ema50",
    "bb_high",
    "bb_low"
    ]
    ]
    .values
    .tolist()
    )

    print("Strategy Loaded:", strategy["strategy_name"]);
    return {
    "signal": signal,
    
    "strategy": strategy["strategy_name"],
    "strategy_version": strategy.get("version", 1),
    "confidence": confidence,
    "reason": f"Multi-factor confluence score: {score}",
    "market_regime": regime,
    "htf_trend": htf_trend,
    "price": round(price, 2),
    "ema20": round(ema20, 2),
    "ema50": round(ema50, 2),
    "rsi": round(rsi, 2),
    "macd": round(macd_val, 3),
    "adx": round(adx, 2),
    "volume_ratio": round(volume_ratio, 2),
    "pcr": round(pcr, 2),
    "oi_change_pct": round(oi_change, 2),
    "buy_threshold": BUY_THRESHOLD,
    "sell_threshold": SELL_THRESHOLD,
    "chart": chart
}
