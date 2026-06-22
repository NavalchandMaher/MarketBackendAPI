from db.mongodb import trades

balance = 10000

def place_trade(
        symbol,
        signal,
        price):

    global balance

    trade = {
        "symbol": symbol,
        "side": signal,
        "entry_price": price,
        "quantity": 1,
        "status": "OPEN"
    }

    trades.insert_one(trade)

    return trade