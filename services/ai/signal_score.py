from typing import Dict


class SignalScore:

    @staticmethod
    def calculate(indicators: Dict, strategy: Dict):

        score = 0
        max_score = 100
        reasons = []

        # -----------------------
        # EMA Trend (20 points)
        # -----------------------
        if indicators["ema_fast"] > indicators["ema_slow"]:
            score += 20
            reasons.append("EMA Bullish")
        else:
            score -= 20
            reasons.append("EMA Bearish")

        # -----------------------
        # RSI (15 points)
        # -----------------------
        rsi = indicators["rsi"]

        if rsi < strategy.get("rsi_buy", 35):
            score += 15
            reasons.append("RSI Oversold")

        elif rsi > strategy.get("rsi_sell", 70):
            score -= 15
            reasons.append("RSI Overbought")

        elif 45 <= rsi <= 55:
            score += 2

        # -----------------------
        # MACD (15 points)
        # -----------------------
        if indicators["macd"] > indicators["macd_signal"]:
            score += 15
            reasons.append("MACD Bullish")
        else:
            score -= 15
            reasons.append("MACD Bearish")

        # -----------------------
        # ADX (10 points)
        # -----------------------
        if indicators["adx"] >= strategy.get("adx_min", 25):
            score += 10
            reasons.append("Strong Trend")
        else:
            score -= 5

        # -----------------------
        # Bollinger Band (10 points)
        # -----------------------
        price = indicators["price"]

        if price < indicators["bb_low"]:
            score += 10
            reasons.append("Below Lower BB")

        elif price > indicators["bb_high"]:
            score -= 10
            reasons.append("Above Upper BB")

        # -----------------------
        # Volume (10 points)
        # -----------------------
        if indicators["volume_ratio"] >= strategy.get("volume_ratio_min", 1.3):
            score += 10
            reasons.append("High Volume")

        # -----------------------
        # PCR (5 points)
        # -----------------------
        pcr = indicators["pcr"]

        if pcr > 1.2:
            score += 5

        elif pcr < 0.8:
            score -= 5

        # -----------------------
        # Open Interest (10 points)
        # -----------------------
        oi = indicators["oi_change_pct"]

        if oi > 2:
            score += 10
            reasons.append("OI Increasing")

        elif oi < -2:
            score -= 10
            reasons.append("OI Decreasing")

        # -----------------------
        # Higher Timeframe (5 points)
        # -----------------------
        if indicators["htf_trend"] == "BULLISH":
            score += 5

        elif indicators["htf_trend"] == "BEARISH":
            score -= 5

        # -----------------------
        # Final Signal
        # -----------------------
        buy_threshold = strategy.get("buy_threshold", 25)
        sell_threshold = strategy.get("sell_threshold", -25)

        if score >= buy_threshold:
            signal = "BUY"

        elif score <= sell_threshold:
            signal = "SELL"

        else:
            signal = "WAIT"

        confidence = min(95, int(abs(score) / max_score * 100))

        return {
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
        }
