import pandas as pd
import ta


class MarketRegime:

    @staticmethod
    def detect(df: pd.DataFrame):
        """
        Detect market regime using latest completed candle.

        Returns:
        {
            "regime": "TRENDING",
            "trend": "BULLISH",
            "strength": "STRONG",
            "volatility": "HIGH"
        }
        """

        data = df.copy()

        # EMA
        data["ema20"] = data["close"].ewm(span=20).mean()
        data["ema50"] = data["close"].ewm(span=50).mean()

        # ADX
        adx = ta.trend.ADXIndicator(
            high=data["high"], low=data["low"], close=data["close"]
        )

        data["adx"] = adx.adx()

        # ATR
        atr = ta.volatility.AverageTrueRange(
            high=data["high"], low=data["low"], close=data["close"]
        )

        data["atr"] = atr.average_true_range()

        candle = data.iloc[-2]

        price = float(candle["close"])
        ema20 = float(candle["ema20"])
        ema50 = float(candle["ema50"])
        adx = float(candle["adx"])
        atr = float(candle["atr"])

        # -----------------------------
        # Trend
        # -----------------------------

        if ema20 > ema50:
            trend = "BULLISH"
        elif ema20 < ema50:
            trend = "BEARISH"
        else:
            trend = "SIDEWAYS"

        # -----------------------------
        # Regime
        # -----------------------------

        if adx >= 30:
            regime = "TRENDING"

        elif adx >= 20:
            regime = "BREAKOUT"

        else:
            regime = "RANGING"

        # -----------------------------
        # Trend Strength
        # -----------------------------

        if adx >= 40:
            strength = "VERY_STRONG"

        elif adx >= 30:
            strength = "STRONG"

        elif adx >= 20:
            strength = "MEDIUM"

        else:
            strength = "WEAK"

        # -----------------------------
        # Volatility
        # -----------------------------

        atr_percent = (atr / price) * 100

        if atr_percent >= 2:
            volatility = "HIGH"

        elif atr_percent >= 1:
            volatility = "MEDIUM"

        else:
            volatility = "LOW"

        return {
            "regime": regime,
            "trend": trend,
            "strength": strength,
            "volatility": volatility,
            "adx": round(adx, 2),
            "atr": round(atr, 2),
            "atr_percent": round(atr_percent, 2),
        }
