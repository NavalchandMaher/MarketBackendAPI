from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from services.signal_engine import analyze_market
from bson import ObjectId
from db.mongodb import paper_trades


from db.mongodb import (
    paper_trades,
    learning_logs,
    strategies
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analysis")
def analysis(
    symbol: str = Query("BTCUSDT"),
    timeframe: str = Query("5m")
):
    return analyze_market(symbol, timeframe)

@app.get("/paper-trades")
def get_trade_dashboard():

    open_trades = paper_trades.count_documents({
        "status": "OPEN"
    })

    closed_trades = paper_trades.count_documents({
        "status": "CLOSED"
    })

    wins = paper_trades.count_documents({
        "status": "CLOSED",
        "win_loss": "WIN"
    })

    losses = paper_trades.count_documents({
        "status": "CLOSED",
        "win_loss": "LOSS"
    })

    win_rate = 0

    if closed_trades > 0:
        win_rate = round(
            (wins / closed_trades) * 100,
            2
        )

    pipeline = [
        {
            "$group": {
                "_id": None,
                "profit": {
                    "$sum": "$profit_loss"
                }
            }
        }
    ]

    result = list(
        paper_trades.aggregate(pipeline)
    )

    total_profit = (
        result[0]["profit"]
        if result
        else 0
    )

    return {
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit": round(total_profit, 2)
    }

@app.get("/paper-trades")
def get_trade_dashboard():

    open_trades = paper_trades.count_documents({
        "status": "OPEN"
    })

    closed_trades = paper_trades.count_documents({
        "status": "CLOSED"
    })

    wins = paper_trades.count_documents({
        "status": "CLOSED",
        "win_loss": "WIN"
    })

    losses = paper_trades.count_documents({
        "status": "CLOSED",
        "win_loss": "LOSS"
    })

    win_rate = 0

    if closed_trades > 0:
        win_rate = round(
            (wins / closed_trades) * 100,
            2
        )

    pipeline = [
        {
            "$group": {
                "_id": None,
                "profit": {
                    "$sum": "$profit_loss"
                }
            }
        }
    ]

    result = list(
        paper_trades.aggregate(pipeline)
    )

    total_profit = (
        result[0]["profit"]
        if result
        else 0
    )

    return {
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit": round(total_profit, 2)
    }

@app.get("/learning-logs")
def get_learning_logs():

    logs = list(
        learning_logs
        .find()
        .sort("created_at", -1)
        .limit(50)
    )

    response = []

    for log in logs:

        response.append({

            "date": str(
                log.get(
                    "created_at",
                    ""
                )
            ),

            "old_threshold":
                log.get(
                    "old_threshold"
                ),

            "new_threshold":
                log.get(
                    "new_threshold"
                ),

            "win_rate":
                log.get(
                    "win_rate"
                ),

            "action":
                log.get(
                    "action"
                )
        })

    return response

@app.get("/strategy")
def current_strategy():

    strategy = strategies.find_one({
        "enabled": True
    })

    if not strategy:

        return {
            "error":
                "No active strategy found"
        }

    return {

        "name":
            strategy.get(
                "strategy_name"
            ),

        "version":
            strategy.get(
                "version"
            ),

        "buy_threshold":
            strategy.get(
                "buy_threshold"
            ),

        "sell_threshold":
            strategy.get(
                "sell_threshold"
            ),

        "tp_percent":
            strategy.get(
                "tp_percent",
                2
            ),

        "sl_percent":
            strategy.get(
                "sl_percent",
                1
            ),

        "ema_fast":
            strategy.get(
                "ema_fast"
            ),

        "ema_slow":
            strategy.get(
                "ema_slow"
            ),

        "rsi_buy":
            strategy.get(
                "rsi_buy"
            ),

        "rsi_sell":
            strategy.get(
                "rsi_sell"
            )
    }

@app.get("/performance")
def performance():

    trades = list(
        paper_trades.find({
            "status": "CLOSED"
        })
    )

    total = len(trades)

    wins = len([
        x for x in trades
        if x.get("profit_loss", 0) > 0
    ])

    profit = sum([
        x.get("profit_loss", 0)
        for x in trades
    ])

    return {
        "total_trades": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate":
            round(
                wins / total * 100,
                2
            ) if total else 0,
        "net_profit":
            round(profit, 2)
    }

@app.get("/paper-trades/history")
def get_trade_history(limit: int = 100):

    trades = list(
        paper_trades
        .find()
        .sort("entry_time", -1)
        .limit(limit)
    )

    response = []

    for trade in trades:

        response.append({

            "id": str(
                trade.get("_id")
            ),

            "symbol":
                trade.get(
                    "symbol"
                ),

            "timeframe":
                trade.get(
                    "timeframe"
                ),

            "strategy_name":
                trade.get(
                    "strategy_name"
                ),

            "strategy_version":
                trade.get(
                    "strategy_version"
                ),

            "signal":
                trade.get(
                    "signal"
                ),

            "entry":
                trade.get(
                    "entry_price",
                    0
                ),

            "exit":
                trade.get(
                    "exit_price",
                    0
                ),

            "stop_loss":
                trade.get(
                    "stop_loss",
                    0
                ),

            "target_price":
                trade.get(
                    "target_price",
                    0
                ),

            "confidence":
                trade.get(
                    "confidence",
                    0
                ),

            "status":
                trade.get(
                    "status",
                    "OPEN"
                ),

            "pnl":
                trade.get(
                    "profit_loss",
                    0
                ),

            "profit_percent":
                trade.get(
                    "profit_percent",
                    0
                ),

            "result":
                trade.get(
                    "win_loss",
                    ""
                ),

            "entry_time":
                str(
                    trade.get(
                        "entry_time"
                    )
                ),

            "exit_time":
                str(
                    trade.get(
                        "exit_time"
                    )
                ),

            "market_regime":
                trade.get(
                    "market_regime"
                )
        })

    return response

