from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from db.mongodb import learning_logs
from services.signal_engine import analyze_market

from services.backtester import BackTester
from db.mongodb import backtest_results

from contextlib import asynccontextmanager
from services.scheduler_service import SchedulerService


from db.mongodb import paper_trades, closed_trades
from services.performance_service import PerformanceService

from services.learning_engine import LearningEngine


@asynccontextmanager
async def lifespan(app: FastAPI):

    SchedulerService.startup()

    yield

    SchedulerService.shutdown()


app = FastAPI(title="Market AI V2", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/analysis")
def analysis(symbol: str = Query("BTCUSDT"), timeframe: str = Query("5m")):
    return analyze_market(symbol, timeframe)


@app.get("/paper-trades")
def get_trade_dashboard():

    open_trades = paper_trades.count_documents({"status": "OPEN"})

    closed_count = closed_trades.count_documents({})

    wins = closed_trades.count_documents({"result": "WIN"})

    losses = closed_trades.count_documents({"result": "LOSS"})

    win_rate = 0

    if closed_count > 0:
        win_rate = round((wins / closed_count) * 100, 2)

    pipeline = [{"$group": {"_id": None, "profit": {"$sum": "$pnl"}}}]

    result = list(closed_trades.aggregate(pipeline))

    total_profit = result[0]["profit"] if result else 0

    return {
        "open_trades": open_trades,
        "closed_trades": closed_count,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_profit": round(total_profit, 2),
    }


@app.get("/learning-logs")
def get_learning_logs():

    logs = list(learning_logs.find().sort("created_at", -1).limit(50))
    response = []

    for log in logs:
        performance = log.get("performance", {})
        response.append(
            {
                "id": str(log.get("_id")),
                "date": str(log.get("created_at")),
                "strategy": log.get("strategy"),
                "version": log.get("version"),
                "buy_threshold": log.get("buy_threshold"),
                "sell_threshold": log.get("sell_threshold"),
                "ema_fast": log.get("ema_fast"),
                "ema_slow": log.get("ema_slow"),
                "rsi_buy": log.get("rsi_buy"),
                "rsi_sell": log.get("rsi_sell"),
                "tp_percent": log.get("tp_percent"),
                "sl_percent": log.get("sl_percent"),
                "performance": {
                    "win_rate": performance.get("win_rate", 0),
                    "wins": performance.get("wins", 0),
                    "losses": performance.get("losses", 0),
                    "total_trades": performance.get("total_trades", 0),
                    "status": performance.get("status", "UNKNOWN"),
                },
            }
        )
    return response


@app.get("/strategy")
def current_strategy():

    strategy = LearningEngine.active_strategy()

    if not strategy:

        return {"error": "No active strategy found"}

    return {
        "name": strategy.get("strategy_name"),
        "version": strategy.get("version"),
        "buy_threshold": strategy.get("buy_threshold"),
        "sell_threshold": strategy.get("sell_threshold"),
        "tp_percent": strategy.get("tp_percent", 2),
        "sl_percent": strategy.get("sl_percent", 1),
        "ema_fast": strategy.get("ema_fast"),
        "ema_slow": strategy.get("ema_slow"),
        "rsi_buy": strategy.get("rsi_buy"),
        "rsi_sell": strategy.get("rsi_sell"),
    }


@app.get("/performance")
def performance():

    return PerformanceService.dashboard()


from itertools import chain


@app.get("/paper-trades/history")
def get_trade_history(limit: int = 100):

    open_list = list(paper_trades.find())
    closed_list = list(closed_trades.find())

    trades = sorted(
        chain(open_list, closed_list), key=lambda x: x.get("entry_time"), reverse=True
    )[:limit]
    response = []

    for trade in trades:
        response.append(
            {
                "id": str(trade.get("_id")),
                "symbol": trade.get("symbol"),
                "timeframe": trade.get("timeframe"),
                "strategy_name": trade.get("strategy_name"),
                "strategy_version": trade.get("strategy_version"),
                "signal": trade.get("signal"),
                "entry": trade.get("entry_price", 0),
                "exit": trade.get("exit_price", 0),
                "stop_loss": trade.get("stop_loss", 0),
                "target_price": trade.get("target_price", 0),
                "confidence": trade.get("confidence", 0),
                "status": trade.get("status", "OPEN"),
                "pnl": trade.get("pnl", 0),
                "pnl_percent": trade.get("pnl_percent", 0),
                "result": trade.get("result", ""),
                "entry_time": str(trade.get("entry_time")),
                "exit_time": str(trade.get("exit_time")),
                "market_regime": trade.get("market_regime"),
            }
        )

    return response


@app.get("/backtest")
def backtest(
    symbol: str = Query("BTCUSDT"), timeframe: str = Query("5m"), days: int = Query(365)
):
    return BackTester.run(symbol=symbol, timeframe=timeframe, days=days)


@app.get("/backtest/history")
def backtest_history():

    data = list(backtest_results.find({}, {"_id": 0}))

    return data


# ============================================================
# Scheduler APIs
# ============================================================


@app.get("/scheduler/status")
def scheduler_status():
    return SchedulerService.status()


@app.get("/scheduler/dashboard")
def scheduler_dashboard():
    return SchedulerService.dashboard()


@app.post("/scheduler/run-market")
def run_market():
    return SchedulerService.run_market_now()


@app.post("/scheduler/run-nightly")
def run_nightly():
    return SchedulerService.run_nightly_now()
