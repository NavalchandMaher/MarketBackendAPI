import ccxt
import pandas as pd
import ta
import requests

from services.learning_engine import LearningEngine
from services.paper_trading import PaperTrading
from services.market_regime import MarketRegime
from db.mongodb import paper_trades

# ============================================================
# BINANCE CONNECTION
# ============================================================

exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})

# ============================================================
# CACHE
# ============================================================

LAST_OI = {}
LAST_PRICE = {}

VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]

# ============================================================
# HELPERS
# ============================================================


def safe(value, default=0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


def validate_timeframe(timeframe):

    if timeframe not in VALID_TIMEFRAMES:
        return "5m"

    return timeframe


# ============================================================
# MARKET DATA
# ============================================================


def get_market_data(symbol, timeframe):

    pair = symbol.replace("USDT", "/USDT")

    candles = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=300)

    df = pd.DataFrame(
        candles, columns=["time", "open", "high", "low", "close", "volume"]
    )

    return df


# ============================================================
# HIGHER TIMEFRAME
# ============================================================


def get_higher_timeframe(symbol):

    pair = symbol.replace("USDT", "/USDT")

    candles = exchange.fetch_ohlcv(pair, timeframe="1h", limit=250)

    df = pd.DataFrame(
        candles, columns=["time", "open", "high", "low", "close", "volume"]
    )

    df["ema50"] = df["close"].ewm(span=50).mean()

    candle = df.iloc[-2]

    if candle["close"] > candle["ema50"]:
        return "BULLISH"

    return "BEARISH"


# ============================================================
# OPEN INTEREST
# ============================================================


def get_open_interest(symbol, price):

    pair = symbol.replace("USDT", "/USDT")

    try:

        oi = exchange.fetch_open_interest(pair)

        current = safe(oi.get("openInterest", 0))

        previous = LAST_OI.get(pair, current)

        previous_price = LAST_PRICE.get(pair, price)

        LAST_OI[pair] = current
        LAST_PRICE[pair] = price

        change = 0

        if current != 0:

            change = ((current - previous) / current) * 100

        return (current, change, previous_price)

    except Exception:

        return (0, 0, price)


# ============================================================
# PUT CALL RATIO
# ============================================================


def get_pcr(symbol):

    try:

        currency = "BTC"

        if "ETH" in symbol:
            currency = "ETH"

        url = (
            "https://www.deribit.com/api/v2/public/"
            "get_book_summary_by_currency"
            f"?currency={currency}&kind=option"
        )

        response = requests.get(url, timeout=5).json()

        result = response["result"]

        call_oi = 0
        put_oi = 0

        for option in result:

            oi = float(option["open_interest"])

            if option["instrument_name"].endswith("C"):

                call_oi += oi

            else:

                put_oi += oi

        if call_oi == 0:
            return 1

        return put_oi / call_oi

    except Exception:

        return 1


# ============================================================
# INDICATOR ENGINE
# ============================================================


def calculate_indicators(df):

    # ---------------- EMA ----------------

    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    df["ema100"] = df["close"].ewm(span=100, adjust=False).mean()

    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    # ---------------- RSI ----------------

    rsi = ta.momentum.RSIIndicator(close=df["close"], window=14)

    df["rsi"] = rsi.rsi()

    # ---------------- MACD ----------------

    macd = ta.trend.MACD(close=df["close"])

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_histogram"] = macd.macd_diff()

    # ---------------- ADX ----------------

    adx = ta.trend.ADXIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=14
    )

    df["adx"] = adx.adx()
    df["plus_di"] = adx.adx_pos()
    df["minus_di"] = adx.adx_neg()

    # ---------------- ATR ----------------

    atr = ta.volatility.AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=14
    )

    df["atr"] = atr.average_true_range()

    # ---------------- Bollinger ----------------

    bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)

    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    # ---------------- Volume ----------------

    df["volume_avg"] = df["volume"].rolling(20).mean()

    df["volume_ratio"] = df["volume"] / df["volume_avg"]

    # ---------------- Trend ----------------

    df["trend"] = "SIDEWAYS"

    df.loc[df["ema20"] > df["ema50"], "trend"] = "BULLISH"

    df.loc[df["ema20"] < df["ema50"], "trend"] = "BEARISH"

    # ---------------- Price Change ----------------

    df["price_change"] = df["close"].pct_change() * 100

    # ---------------- Candle Body ----------------

    df["body"] = abs(df["close"] - df["open"])

    # ---------------- Upper Wick ----------------

    df["upper_wick"] = df["high"] - df[["close", "open"]].max(axis=1)

    # ---------------- Lower Wick ----------------

    df["lower_wick"] = df[["close", "open"]].min(axis=1) - df["low"]

    # ---------------- Volatility ----------------

    df["volatility"] = ((df["high"] - df["low"]) / df["close"]) * 100

    # ---------------- Remove NaN ----------------

    df.bfill(inplace=True)
    df.ffill(inplace=True)

    return df


# ============================================================
# ANALYZE MARKET
# ============================================================


def analyze_market(symbol="BTCUSDT", timeframe="5m", user_id=None):

    # ---------------------------------------
    # VALIDATE TIMEFRAME
    # ---------------------------------------

    timeframe = validate_timeframe(timeframe)

    # ---------------------------------------
    # LOAD MARKET DATA
    # ---------------------------------------

    df = get_market_data(symbol, timeframe)

    if df.empty:
        return {"error": "No market data found."}

    if len(df) < 250:
        return {"error": "Not enough candles."}

    # ---------------------------------------
    # CALCULATE INDICATORS
    # ---------------------------------------

    df = calculate_indicators(df)

    # ---------------------------------------
    # CURRENT CANDLE
    # ---------------------------------------

    candle = df.iloc[-2]

    # ---------------------------------------
    # PRICE
    # ---------------------------------------

    price = safe(candle["close"])

    # ---------------------------------------
    # HIGHER TIMEFRAME
    # ---------------------------------------

    htf_trend = get_higher_timeframe(symbol)

    # ---------------------------------------
    # OPEN INTEREST
    # ---------------------------------------

    current_oi, oi_change, previous_price = get_open_interest(symbol, price)

    # ---------------------------------------
    # PCR
    # ---------------------------------------

    pcr = get_pcr(symbol)

    # ---------------------------------------
    # LOAD STRATEGY
    # ---------------------------------------

    # Strategies are user-scoped.  Resolving without the user ID falls back to
    # the globally active strategy, which can produce a signal for a different
    # user's configuration.
    strategy = LearningEngine.active_strategy(user_id=user_id) or {}

    strategy_parameters = strategy.get("indicator_parameters", {}) or {}

    strategy_name = strategy.get("strategy_name", strategy.get("name", "EMA_MACD_V1"))

    strategy_version = strategy.get("version", 1)

    BUY_THRESHOLD = strategy.get(
        "buy_threshold", strategy_parameters.get("buy_threshold", 3)
    )

    SELL_THRESHOLD = strategy.get(
        "sell_threshold", strategy_parameters.get("sell_threshold", -3)
    )

    TP_PERCENT = strategy.get(
        "tp_percent", strategy.get("tp", strategy_parameters.get("tp_percent", 2))
    )

    SL_PERCENT = strategy.get(
        "sl_percent", strategy.get("sl", strategy_parameters.get("sl_percent", 1))
    )

    # ---------------------------------------
    # EXTRACT INDICATORS
    # ---------------------------------------

    ema20 = safe(candle["ema20"])

    ema50 = safe(candle["ema50"])

    ema100 = safe(candle["ema100"])

    ema200 = safe(candle["ema200"])

    rsi = safe(candle["rsi"])

    macd = safe(candle["macd"])

    macd_signal = safe(candle["macd_signal"])

    adx = safe(candle["adx"])

    atr = safe(candle["atr"])

    volume_ratio = safe(candle["volume_ratio"], 1)

    bb_upper = safe(candle["bb_upper"])

    bb_lower = safe(candle["bb_lower"])

    # ---------------------------------------
    # MARKET REGIME
    # ---------------------------------------

    regime_info = MarketRegime.detect(df)
    regime = regime_info["regime"]

    # ---------------------------------------
    # SCORE VARIABLES
    # ---------------------------------------

    score = 0

    score_details = []

    max_score = 15

    # ============================================================
    # EMA SCORING
    # ============================================================

    if ema20 > ema50:
        score += 2
        score_details.append("EMA20 > EMA50 (+2)")
    else:
        score -= 2
        score_details.append("EMA20 < EMA50 (-2)")

    if ema50 > ema100:
        score += 1
        score_details.append("EMA50 > EMA100 (+1)")
    else:
        score -= 1
        score_details.append("EMA50 < EMA100 (-1)")

    if ema100 > ema200:
        score += 1
        score_details.append("EMA100 > EMA200 (+1)")
    else:
        score -= 1
        score_details.append("EMA100 < EMA200 (-1)")

    # ============================================================
    # RSI
    # ============================================================

    if rsi < 30:
        score += 2
        score_details.append("RSI Oversold (+2)")

    elif rsi < 40:
        score += 1
        score_details.append("RSI Buy Zone (+1)")

    elif rsi > 70:
        score -= 2
        score_details.append("RSI Overbought (-2)")

    elif rsi > 60:
        score -= 1
        score_details.append("RSI Sell Zone (-1)")

    # ============================================================
    # MACD
    # ============================================================

    if macd > macd_signal:
        score += 2
        score_details.append("MACD Bullish (+2)")
    else:
        score -= 2
        score_details.append("MACD Bearish (-2)")

    # ============================================================
    # ADX
    # ============================================================

    if adx >= 30:
        score += 2
        score_details.append("Strong Trend (+2)")

    elif adx >= 25:
        score += 1
        score_details.append("Trending (+1)")

    else:
        score_details.append("Weak Trend")

    # ============================================================
    # VOLUME
    # ============================================================

    if volume_ratio >= 2:
        score += 2
        score_details.append("Very High Volume (+2)")

    elif volume_ratio >= 1.5:
        score += 1
        score_details.append("High Volume (+1)")

    # ============================================================
    # OPEN INTEREST
    # ============================================================

    if oi_change >= 3:
        score += 2
        score_details.append("OI Rising (+2)")

    elif oi_change >= 1:
        score += 1
        score_details.append("OI Increasing (+1)")

    elif oi_change <= -3:
        score -= 2
        score_details.append("OI Falling (-2)")

    # ============================================================
    # PCR
    # ============================================================

    if pcr > 1.20:
        score += 1
        score_details.append("Bullish PCR (+1)")

    elif pcr < 0.80:
        score -= 1
        score_details.append("Bearish PCR (-1)")

    # ============================================================
    # HIGHER TIMEFRAME CONFIRMATION
    # ============================================================

    if htf_trend == "BULLISH":
        score += 2
        score_details.append("HTF Bullish (+2)")

    elif htf_trend == "BEARISH":
        score -= 2
        score_details.append("HTF Bearish (-2)")

    # ============================================================
    # MARKET REGIME ADJUSTMENT
    # ============================================================

    if regime == "TRENDING":
        score += 1
        score_details.append("Trending Market (+1)")

    elif regime == "RANGING":
        score = int(score * 0.70)
        score_details.append("Range Market (Score Reduced)")

    # ============================================================
    # SIGNAL
    # ============================================================

    if score >= BUY_THRESHOLD:

        signal = "BUY"

    elif score <= SELL_THRESHOLD:

        signal = "SELL"

    else:

        signal = "WAIT"

    # ============================================================
    # CONFIDENCE
    # ============================================================

    confidence = min(95, max(5, int(abs(score) / max_score * 100)))

    # ============================================================
    # LEARNING SNAPSHOT
    # ============================================================

    snapshot = {
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
        "ema100": round(ema100, 2),
        "ema200": round(ema200, 2),
        "rsi": round(rsi, 2),
        "macd": round(macd, 4),
        "macd_signal": round(macd_signal, 4),
        "adx": round(adx, 2),
        "atr": round(atr, 2),
        "pcr": round(pcr, 2),
        "volume_ratio": round(volume_ratio, 2),
        "oi_change": round(oi_change, 2),
        "score": score,
        "market_regime": regime,
        "higher_timeframe": htf_trend,
    }

    # ============================================================
    # PAPER TRADING
    # ============================================================

    open_trade = paper_trades.find_one(
        {"symbol": symbol, "timeframe": timeframe, "status": "OPEN"}
    )

    if signal != "WAIT" and open_trade is None:

        PaperTrading.open_trade(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy_name": strategy_name,
                "strategy_version": strategy_version,
                "signal": signal,
                "entry_price": price,
                "confidence": confidence,
                "market_regime": regime,
                "tp_percent": TP_PERCENT,
                "sl_percent": SL_PERCENT,
                "indicators": snapshot,
            }
        )

    # ============================================================
    # CURRENT PAPER TRADE
    # ============================================================

    open_trade = paper_trades.find_one(
        {"symbol": symbol, "timeframe": timeframe, "status": "OPEN"}
    )

    trade_info = None

    if open_trade:

        trade_info = {
            "signal": open_trade.get("signal"),
            "entry_price": round(open_trade.get("entry_price", 0), 2),
            "take_profit": round(open_trade.get("take_profit", 0), 2),
            "stop_loss": round(open_trade.get("stop_loss", 0), 2),
            "opened_at": str(open_trade.get("opened_at")),
        }

    # ============================================================
    # CHART DATA
    # ============================================================

    chart = df.tail(100)[
        ["time", "close", "ema20", "ema50", "bb_upper", "bb_lower"]
    ].values.tolist()

    # ============================================================
    # FINAL RESPONSE
    # ============================================================

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "reason": ", ".join(score_details),
        "strategy": {
            "name": strategy_name,
            "version": strategy_version,
            "buy_threshold": BUY_THRESHOLD,
            "sell_threshold": SELL_THRESHOLD,
            "tp_percent": TP_PERCENT,
            "sl_percent": SL_PERCENT,
        },
        "market_regime": regime,
        "higher_timeframe": htf_trend,
        "price": round(price, 2),
        "indicators": {
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema100": round(ema100, 2),
            "ema200": round(ema200, 2),
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "adx": round(adx, 2),
            "atr": round(atr, 2),
            "pcr": round(pcr, 2),
            "volume_ratio": round(volume_ratio, 2),
            "oi_change_pct": round(oi_change, 2),
        },
        "paper_trade": trade_info,
        "chart": chart,
    }
