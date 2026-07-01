from db.mongodb import paper_trades

def close_trade(trade, current_price):

    pnl = 0

    if trade["signal"] == "BUY":
        pnl = current_price - trade["entry_price"]

    if trade["signal"] == "SELL":
        pnl = trade["entry_price"] - current_price

    paper_trades.update_one(
        {"_id": trade["_id"]},
        {
            "$set": {
                "status": "CLOSED",
                "exit_price": current_price,
                "pnl": pnl,
                "result": "WIN" if pnl > 0 else "LOSS"
            }
        }
    )