from typing import Dict


class RiskManager:

    DEFAULT_RISK_PERCENT = 2.0
    DEFAULT_RISK_REWARD = 2.0

    @staticmethod
    def calculate_trade(
        signal: str, entry_price: float, strategy: Dict, account_balance: float = 100000
    ):

        tp_percent = strategy.get("tp_percent", 2)
        sl_percent = strategy.get("sl_percent", 1)
        risk_percent = strategy.get("risk_percent", RiskManager.DEFAULT_RISK_PERCENT)

        risk_reward = tp_percent / sl_percent

        if signal == "BUY":

            stop_loss = entry_price * (1 - sl_percent / 100)

            take_profit = entry_price * (1 + tp_percent / 100)

        elif signal == "SELL":

            stop_loss = entry_price * (1 + sl_percent / 100)

            take_profit = entry_price * (1 - tp_percent / 100)

        else:

            return None

        capital_at_risk = account_balance * risk_percent / 100

        stop_distance = abs(entry_price - stop_loss)

        quantity = 0

        if stop_distance > 0:

            quantity = capital_at_risk / stop_distance

        expected_loss = quantity * stop_distance

        expected_profit = quantity * abs(take_profit - entry_price)

        return {
            "signal": signal,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward": round(risk_reward, 2),
            "quantity": round(quantity, 4),
            "capital_at_risk": round(capital_at_risk, 2),
            "expected_profit": round(expected_profit, 2),
            "expected_loss": round(expected_loss, 2),
        }

    @staticmethod
    def calculate_using_atr(
        signal: str, entry_price: float, atr: float, multiplier: float = 2.0
    ):

        if signal == "BUY":

            stop_loss = entry_price - atr * multiplier

            take_profit = entry_price + atr * multiplier * 2

        else:

            stop_loss = entry_price + atr * multiplier

            take_profit = entry_price - atr * multiplier * 2

        return {"stop_loss": round(stop_loss, 2), "take_profit": round(take_profit, 2)}

    @staticmethod
    def validate_trade(confidence: int, market_regime: str, adx: float):

        if confidence < 60:

            return (False, "Low confidence")

        if market_regime == "RANGING":

            return (False, "Market is ranging")

        if adx < 20:

            return (False, "Weak trend")

        return (True, "Trade Accepted")
