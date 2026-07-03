"""
MongoDB Connection Manager
Market AI V2
"""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure

# ==========================================================
# CONFIG
# ==========================================================

MONGO_URI = "mongodb://localhost:27017"

DATABASE_NAME = "MarketAI_V2"

# ==========================================================
# CONNECT
# ==========================================================

try:

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    client.admin.command("ping")

    print("MongoDB Connected Successfully")

except ConnectionFailure as e:

    print("MongoDB Connection Failed")

    print(e)

    raise e

# ==========================================================
# DATABASE
# ==========================================================

db = client[DATABASE_NAME]

# ==========================================================
# COLLECTIONS
# ==========================================================

paper_trades = db["paper_trades"]

closed_trades = db["closed_trades"]

strategies = db["strategies"]

performance = db["performance"]

learning_logs = db["learning_logs"]

backtest_results = db["backtest_results"]

market_snapshots = db["market_snapshots"]

daily_reports = db["daily_reports"]

strategy_history = db["strategy_history"]

users = db["users"]

settings = db["settings"]

notifications = db["notifications"]

scheduler_logs = db["scheduler_logs"]

# ==========================================================
# INDEXES
# ==========================================================

paper_trades.create_index([("symbol", ASCENDING), ("status", ASCENDING)])

paper_trades.create_index([("created_at", ASCENDING)])

closed_trades.create_index([("symbol", ASCENDING)])

closed_trades.create_index([("closed_at", ASCENDING)])

strategies.create_index([("strategy_name", ASCENDING)], unique=True)

strategies.create_index([("enabled", ASCENDING)])

performance.create_index([("date", ASCENDING)], unique=True)

learning_logs.create_index([("created_at", ASCENDING)])

backtest_results.create_index([("strategy_name", ASCENDING), ("symbol", ASCENDING)])

market_snapshots.create_index([("symbol", ASCENDING), ("created_at", ASCENDING)])

strategy_history.create_index([("strategy_name", ASCENDING), ("version", ASCENDING)])

scheduler_logs.create_index([("job_name", ASCENDING), ("run_time", ASCENDING)])

# ==========================================================
# DEFAULT STRATEGY
# ==========================================================

default_strategy = {
    "name": "EMA_MACD_V1",
    "version": 1,
    "enabled": True,
    "buy_threshold": 3,
    "sell_threshold": -3,
    "ema_fast": 20,
    "ema_slow": 50,
    "ema_long": 200,
    "rsi_buy": 40,
    "rsi_sell": 65,
    "adx_min": 25,
    "volume_ratio_min": 1.30,
    "tp_percent": 2.0,
    "sl_percent": 1.0,
    "risk_reward": 2,
    "max_open_trades": 3,
    "created_by": "SYSTEM",
}

if strategies.count_documents({"enabled": True}) == 0:

    strategies.insert_one(default_strategy)

    print("Default Strategy Created")

# ==========================================================
# DEFAULT SETTINGS
# ==========================================================

if settings.count_documents({}) == 0:

    settings.insert_one(
        {
            "paper_trading": True,
            "auto_learning": True,
            "auto_backtest": True,
            "scheduler_enabled": True,
            "market": "BINANCE",
            "default_symbol": "BTCUSDT",
            "default_timeframe": "5m",
            "max_backtest_days": 365,
        }
    )

    print("Default Settings Created")

# ==========================================================
# HEALTH CHECK
# ==========================================================


def check_connection():

    try:

        client.admin.command("ping")

        return True

    except Exception:

        return False


# ==========================================================
# DATABASE STATS
# ==========================================================


def database_status():

    return {
        "connected": check_connection(),
        "database": DATABASE_NAME,
        "collections": {
            "paper_trades": paper_trades.count_documents({}),
            "closed_trades": closed_trades.count_documents({}),
            "strategies": strategies.count_documents({}),
            "performance": performance.count_documents({}),
            "learning_logs": learning_logs.count_documents({}),
            "backtest_results": backtest_results.count_documents({}),
        },
    }
