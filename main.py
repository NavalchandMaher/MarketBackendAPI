from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from services.signal_engine import analyze_market

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

