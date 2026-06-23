from datetime import datetime
from db.mongodb import paper_trades


class PaperTrading:

    @staticmethod
    def open_trade(signal_data):

        price = signal_data["price"]
        signal = signal_data["signal"]

        # Default Risk Management
        if signal == "BUY":
            stop_loss = round(price * 0.99, 2)
            target_price = round(price * 1.02, 2)
        else:
            stop_loss = round(price * 1.01, 2)
            target_price = round(price * 0.98, 2)

        trade = {

            "symbol": signal_data.get("symbol"),

            "timeframe":
                signal_data.get(
                    "timeframe",
                    "5m"
                ),

            "strategy_name":
                signal_data.get(
                    "strategy_name",
                    "EMA_MACD_V1"
                ),

            "strategy_version":
                signal_data.get(
                    "strategy_version",
                    1
                ),

            "signal": signal,

            "entry_price": price,

            "exit_price": None,

            "stop_loss": stop_loss,

            "target_price": target_price,

            "confidence":
                signal_data.get(
                    "confidence",
                    0
                ),

            "status": "OPEN",

            "profit_loss": 0,

            "profit_percent": 0,

            "win_loss": None,

            "entry_time":
                datetime.utcnow(),

            "exit_time": None,

            "market_regime":
                signal_data.get(
                    "market_regime",
                    "UNKNOWN"
                ),

            "indicators":
                signal_data.get(
                    "indicators",
                    {}
                )
        }

        result = paper_trades.insert_one(
            trade
        )

        return str(
            result.inserted_id
        )

    @staticmethod
    def close_trade(
        trade_id,
        exit_price
    ):

        trade = paper_trades.find_one(
            {"_id": trade_id}
        )

        if not trade:
            return

        entry_price = trade[
            "entry_price"
        ]

        pnl = (
            exit_price
            - entry_price
        )

        # Reverse PNL for SELL
        if trade["signal"] == "SELL":
            pnl = pnl * -1

        pnl_percent = (
            pnl / entry_price
        ) * 100

        win_loss = (
            "WIN"
            if pnl > 0
            else "LOSS"
        )

        paper_trades.update_one(
            {"_id": trade_id},
            {
                "$set": {

                    "status":
                        "CLOSED",

                    "exit_price":
                        round(
                            exit_price,
                            2
                        ),

                    "profit_loss":
                        round(
                            pnl,
                            2
                        ),

                    "profit_percent":
                        round(
                            pnl_percent,
                            2
                        ),

                    "win_loss":
                        win_loss,

                    "exit_time":
                        datetime.utcnow()
                }
            }
        )

    @staticmethod
    def create_trade(signal_data):
        """
        Backward compatibility
        """

        return PaperTrading.open_trade(
            signal_data
        )