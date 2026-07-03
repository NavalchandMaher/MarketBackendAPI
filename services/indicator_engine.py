"""
Indicator Engine
Market AI V2
"""

import numpy as np
import pandas as pd
import ta

# ==========================================================
# SAFE VALUE
# ==========================================================


def safe(value, default=0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


# ==========================================================
# EMA
# ==========================================================


def ema(df, period):

    return df["close"].ewm(span=period, adjust=False).mean()


# ==========================================================
# RSI
# ==========================================================


def rsi(df, period=14):

    indicator = ta.momentum.RSIIndicator(close=df["close"], window=period)

    return indicator.rsi()


# ==========================================================
# MACD
# ==========================================================


def macd(df):

    indicator = ta.trend.MACD(close=df["close"])

    df["macd"] = indicator.macd()

    df["macd_signal"] = indicator.macd_signal()

    df["macd_histogram"] = indicator.macd_diff()

    return df


# ==========================================================
# SMA
# ==========================================================


def sma(df, period):

    return df["close"].rolling(period).mean()


# ==========================================================
# PRICE CHANGE %
# ==========================================================


def price_change(df):

    return df["close"].pct_change() * 100


# ==========================================================
# VOLUME CHANGE %
# ==========================================================


def volume_change(df):

    return df["volume"].pct_change() * 100


# ==========================================================
# CROSSOVER
# ==========================================================


def crossover(fast, slow):

    return (fast.shift(1) <= slow.shift(1)) & (fast > slow)


# ==========================================================
# CROSSUNDER
# ==========================================================


def crossunder(fast, slow):

    return (fast.shift(1) >= slow.shift(1)) & (fast < slow)


# ==========================================================
# EMA TREND
# ==========================================================


def ema_trend(df):

    if df.iloc[-1]["ema20"] > df.iloc[-1]["ema50"]:

        return "BULLISH"

    elif df.iloc[-1]["ema20"] < df.iloc[-1]["ema50"]:

        return "BEARISH"

    return "SIDEWAYS"


# ==========================================================
# MACD TREND
# ==========================================================


def macd_trend(df):

    if df.iloc[-1]["macd"] > df.iloc[-1]["macd_signal"]:

        return "BULLISH"

    return "BEARISH"


# ==========================================================
# RSI TREND
# ==========================================================


def rsi_trend(df):

    value = safe(df.iloc[-1]["rsi"])

    if value > 60:

        return "BULLISH"

    elif value < 40:

        return "BEARISH"

    return "NEUTRAL"


# ==========================================================
# BASIC INDICATORS
# ==========================================================


def prepare_basic_indicators(df):

    df["ema20"] = ema(df, 20)

    df["ema50"] = ema(df, 50)

    df["ema100"] = ema(df, 100)

    df["ema200"] = ema(df, 200)

    df["sma20"] = sma(df, 20)

    df["sma50"] = sma(df, 50)

    df["rsi"] = rsi(df)

    df = macd(df)

    df["price_change"] = price_change(df)

    df["volume_change"] = volume_change(df)

    return df


# ==========================================================
# ATR
# ==========================================================


def atr(df, period=14):

    indicator = ta.volatility.AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=period
    )

    return indicator.average_true_range()


# ==========================================================
# ADX
# ==========================================================


def adx(df, period=14):

    indicator = ta.trend.ADXIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=period
    )

    df["adx"] = indicator.adx()

    df["plus_di"] = indicator.adx_pos()

    df["minus_di"] = indicator.adx_neg()

    return df


# ==========================================================
# BOLLINGER BAND
# ==========================================================


def bollinger(df):

    bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)

    df["bb_upper"] = bb.bollinger_hband()

    df["bb_middle"] = bb.bollinger_mavg()

    df["bb_lower"] = bb.bollinger_lband()

    df["bb_width"] = df["bb_upper"] - df["bb_lower"]

    return df


# ==========================================================
# VWAP
# ==========================================================


def vwap(df):

    indicator = ta.volume.VolumeWeightedAveragePrice(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"],
        window=14,
    )

    return indicator.volume_weighted_average_price()


# ==========================================================
# VOLUME RATIO
# ==========================================================


def volume_ratio(df):

    average = df["volume"].rolling(20).mean()

    return df["volume"] / average


# ==========================================================
# VOLATILITY
# ==========================================================


def volatility(df):

    return ((df["high"] - df["low"]) / df["close"]) * 100


# ==========================================================
# TREND STRENGTH
# ==========================================================


def trend_strength(df):

    last = df.iloc[-1]

    adx_value = safe(last["adx"])

    if adx_value >= 40:

        return "VERY_STRONG"

    elif adx_value >= 30:

        return "STRONG"

    elif adx_value >= 25:

        return "MEDIUM"

    elif adx_value >= 20:

        return "WEAK"

    return "SIDEWAYS"


# ==========================================================
# PREPARE ADVANCED INDICATORS
# ==========================================================


def prepare_advanced_indicators(df):

    df["atr"] = atr(df)

    df = adx(df)

    df = bollinger(df)

    df["vwap"] = vwap(df)

    df["volume_ratio"] = volume_ratio(df)

    df["volatility"] = volatility(df)

    return df


# ==========================================================
# SUPER TREND
# ==========================================================


def supertrend(df, period=10, multiplier=3):

    atr_value = atr(df, period)

    hl2 = (df["high"] + df["low"]) / 2

    upperband = hl2 + (multiplier * atr_value)

    lowerband = hl2 - (multiplier * atr_value)

    trend = []

    direction = []

    current = 1

    for i in range(len(df)):

        if i == 0:

            trend.append(lowerband.iloc[i])

            direction.append("BULLISH")

            continue

        if df["close"].iloc[i] > upperband.iloc[i - 1]:

            current = 1

        elif df["close"].iloc[i] < lowerband.iloc[i - 1]:

            current = -1

        if current == 1:

            trend.append(lowerband.iloc[i])

            direction.append("BULLISH")

        else:

            trend.append(upperband.iloc[i])

            direction.append("BEARISH")

    df["supertrend"] = trend

    df["supertrend_direction"] = direction

    return df


# ==========================================================
# MOMENTUM
# ==========================================================


def momentum(df, period=10):

    indicator = ta.momentum.ROCIndicator(close=df["close"], window=period)

    return indicator.roc()


# ==========================================================
# OBV
# ==========================================================


def obv(df):

    indicator = ta.volume.OnBalanceVolumeIndicator(
        close=df["close"], volume=df["volume"]
    )

    return indicator.on_balance_volume()


# ==========================================================
# MFI
# ==========================================================


def mfi(df, period=14):

    indicator = ta.volume.MFIIndicator(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"],
        window=period,
    )

    return indicator.money_flow_index()


# ==========================================================
# STOCHASTIC RSI
# ==========================================================


def stochastic_rsi(df, period=14):

    indicator = ta.momentum.StochRSIIndicator(
        close=df["close"], window=period, smooth1=3, smooth2=3
    )

    df["stoch_rsi"] = indicator.stochrsi()

    df["stoch_k"] = indicator.stochrsi_k()

    df["stoch_d"] = indicator.stochrsi_d()

    return df


# ==========================================================
# CCI
# ==========================================================


def cci(df, period=20):

    indicator = ta.trend.CCIIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=period
    )

    return indicator.cci()


# ==========================================================
# WILLIAMS %R
# ==========================================================


def williams_r(df, period=14):

    indicator = ta.momentum.WilliamsRIndicator(
        high=df["high"], low=df["low"], close=df["close"], lbp=period
    )

    return indicator.williams_r()


# ==========================================================
# AWESOME OSCILLATOR
# ==========================================================


def awesome_oscillator(df):

    indicator = ta.momentum.AwesomeOscillatorIndicator(high=df["high"], low=df["low"])

    return indicator.awesome_oscillator()


# ==========================================================
# PREPARE MOMENTUM INDICATORS
# ==========================================================


def prepare_momentum_indicators(df):

    df = supertrend(df)

    df["momentum"] = momentum(df)

    df["obv"] = obv(df)

    df["mfi"] = mfi(df)

    df = stochastic_rsi(df)

    df["cci"] = cci(df)

    df["williams_r"] = williams_r(df)

    df["awesome"] = awesome_oscillator(df)

    return df


# ==========================================================
# SUPPORT & RESISTANCE
# ==========================================================


def support_resistance(df, period=20):

    support = df["low"].rolling(period).min()

    resistance = df["high"].rolling(period).max()

    df["support"] = support
    df["resistance"] = resistance

    return df


# ==========================================================
# PIVOT POINTS
# ==========================================================


def pivot_points(df):

    pivot = (df["high"] + df["low"] + df["close"]) / 3

    df["pivot"] = pivot

    df["r1"] = (2 * pivot) - df["low"]
    df["s1"] = (2 * pivot) - df["high"]

    df["r2"] = pivot + (df["high"] - df["low"])

    df["s2"] = pivot - (df["high"] - df["low"])

    return df


# ==========================================================
# FIBONACCI LEVELS
# ==========================================================


def fibonacci_levels(df):

    high = df["high"].max()
    low = df["low"].min()

    diff = high - low

    return {
        "0.236": high - diff * 0.236,
        "0.382": high - diff * 0.382,
        "0.500": high - diff * 0.500,
        "0.618": high - diff * 0.618,
        "0.786": high - diff * 0.786,
    }


# ==========================================================
# CANDLESTICK PATTERNS
# ==========================================================


def candlestick_patterns(df):

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])

    candle = last["high"] - last["low"]

    upper = last["high"] - max(last["open"], last["close"])

    lower = min(last["open"], last["close"]) - last["low"]

    pattern = "NONE"

    if body < candle * 0.20:

        pattern = "DOJI"

    elif lower > body * 2:

        pattern = "HAMMER"

    elif upper > body * 2:

        pattern = "SHOOTING_STAR"

    elif last["close"] > last["open"] and body > candle * 0.60:

        pattern = "BULLISH"

    elif last["close"] < last["open"] and body > candle * 0.60:

        pattern = "BEARISH"

    return pattern


# ==========================================================
# TREND SUMMARY
# ==========================================================


def trend_summary(df):

    return {
        "ema": ema_trend(df),
        "macd": macd_trend(df),
        "rsi": rsi_trend(df),
        "strength": trend_strength(df),
        "supertrend": df.iloc[-1]["supertrend_direction"],
    }


# ==========================================================
# SIGNAL SUMMARY
# ==========================================================


def signal_summary(df):

    last = df.iloc[-1]

    return {
        "price": safe(last["close"]),
        "ema20": safe(last["ema20"]),
        "ema50": safe(last["ema50"]),
        "rsi": safe(last["rsi"]),
        "macd": safe(last["macd"]),
        "macd_signal": safe(last["macd_signal"]),
        "adx": safe(last["adx"]),
        "atr": safe(last["atr"]),
        "vwap": safe(last["vwap"]),
        "support": safe(last["support"]),
        "resistance": safe(last["resistance"]),
        "pattern": candlestick_patterns(df),
    }


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================


def calculate_all_indicators(df):

    df = prepare_basic_indicators(df)

    df = prepare_advanced_indicators(df)

    df = prepare_momentum_indicators(df)

    df = support_resistance(df)

    df = pivot_points(df)

    summary = signal_summary(df)

    summary["trend"] = trend_summary(df)

    summary["fibonacci"] = fibonacci_levels(df)

    return df, summary
