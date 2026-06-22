from datetime import datetime
from db.mongodb import paper_trades

class PaperTrading:

    @staticmethod
    def open_trade(signal_data):

        trade = {
            "symbol": signal_data["symbol"],
            "signal": signal_data["signal"],
            "entry_price": signal_data["price"],
            "confidence": signal_data["confidence"],
            "status": "OPEN",
            "created_at": datetime.utcnow()
        }

        paper_trades.insert_one(trade)

    @staticmethod
    def close_trade(trade_id, exit_price):

        trade = paper_trades.find_one({"_id": trade_id})

        if not trade:
            return

        pnl = exit_price - trade["entry_price"]

        paper_trades.update_one(
            {"_id": trade_id},
            {
                "$set": {
                    "status": "CLOSED",
                    "exit_price": exit_price,
                    "profit_loss": pnl,
                    "closed_at": datetime.utcnow()
                }
            }
        )
    def create_trade(signal_data):

        trade = {
            "symbol": signal_data.get("symbol"),
            "signal": signal_data.get("signal"),
            "entry_price": signal_data.get("price"),
            "confidence": signal_data.get("confidence", 0),
            "status": "OPEN",
            "created_at": datetime.utcnow()
        }

        paper_trades.insert_one(trade)

        return trade