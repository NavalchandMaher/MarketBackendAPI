"""
MongoDB Connection Manager
Market AI V2
"""

from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from config import DATABASE_NAME, MONGO_URI

# ==========================================================
# CONFIG
# ==========================================================

# ==========================================================
# CONNECT
# ==========================================================

try:

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)

    client.admin.command("ping")

    connected = True

    print("MongoDB Connected Successfully")

except Exception as e:

    connected = False

    print("MongoDB Connection Failed")

    print(e)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)

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
user_settings = db["user_settings"]
user_broker = db["user_broker"]
user_account = db["user_account"]
refresh_tokens = db["refresh_tokens"]

settings = db["settings"]

notifications = db["notifications"]

scheduler_logs = db["scheduler_logs"]

# Records one-time bootstrap actions.  This prevents a deleted template from
# being silently recreated during a later application restart.
bootstrap_state = db["bootstrap_state"]

# ==========================================================
# INDEXES
# ==========================================================

if connected:

    paper_trades.create_index([("symbol", ASCENDING), ("status", ASCENDING)])

    paper_trades.create_index([("created_at", ASCENDING)])

    closed_trades.create_index([("symbol", ASCENDING)])

    closed_trades.create_index([("closed_at", ASCENDING)])

    # Strategy names are private to a user. System strategies use user_id=None,
    # so this compound unique index permits a user strategy to share a name with
    # a global system strategy while still preventing duplicate names per owner.
    #
    # Older deployments used either `name` or `strategy_name` as a globally
    # unique field.  New documents only have `strategy_name`; leaving the old
    # `name` index in place makes every insert after the first fail with
    # DuplicateKeyError for `name: null`.
    strategy_indexes = strategies.index_information()
    for index_name, index in strategy_indexes.items():
        index_key = index.get("key", {})
        key = list(index_key.items()) if hasattr(index_key, "items") else list(index_key)
        if index.get("unique") and key in ([('name', 1)], [('strategy_name', 1)]):
            strategies.drop_index(index_name)
    strategies.create_index([("user_id", ASCENDING), ("strategy_name", ASCENDING)], unique=True)

    strategies.create_index([("enabled", ASCENDING)])

    performance.create_index([("date", ASCENDING)], unique=True)

    learning_logs.create_index([("created_at", ASCENDING)])

    backtest_results.create_index([("strategy_name", ASCENDING), ("symbol", ASCENDING)])

    # User scoping indexes for faster user-specific queries
    backtest_results.create_index([("user_id", ASCENDING)])
    paper_trades.create_index([("user_id", ASCENDING)])
    closed_trades.create_index([("user_id", ASCENDING)])
    learning_logs.create_index([("user_id", ASCENDING)])
    notifications.create_index([("user_id", ASCENDING)])
    settings.create_index([("user_id", ASCENDING)])

    market_snapshots.create_index([("symbol", ASCENDING), ("created_at", ASCENDING)])

    strategy_history.create_index([("strategy_name", ASCENDING), ("version", ASCENDING)])

    scheduler_logs.create_index([("job_name", ASCENDING), ("run_time", ASCENDING)])

# ==========================================================
# DEFAULT SYSTEM STRATEGY
# ==========================================================

# This is a bootstrap template, not a hardcoded runtime strategy.  Once it is
# in MongoDB it is managed like every other System strategy: Admins can edit,
# publish/unpublish, or delete it through the API.
DEFAULT_SYSTEM_STRATEGY_NAME = "EMA_MACD_V1"
DEFAULT_SYSTEM_STRATEGY_SEED_MARKER = "default_system_strategy_seeded"

default_strategy = {
    "strategy_name": DEFAULT_SYSTEM_STRATEGY_NAME,
    "version": 1,
    "enabled": True,
    "is_default": True,
    "paper_mode": True,
    "live_mode": False,
    "priority": 1,
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "strategy_type": "System",
    "exchange": "BINANCE",
    "description": "Default EMA_MACD_V1 strategy",
    "risk_percent": 1.0,
    "tp": 2.0,
    "sl": 1.0,
    "indicator_parameters": {
        "buy_conditions": [
            {
                "id": "90f1a077-3f54-4dbe-897d-edd302fe45bb",
                "indicator": {
                    "id": "ema",
                    "name": "EMA",
                    "category": "Trend",
                    "parameter": {
                        "fast": 20,
                        "slow": 50,
                        "source": "Close",
                        "condition": "Bullish Cross"
                    },
                    "applyTo": "buy"
                },
                "enabled": True
            },
            {
                "id": "44676baa-df16-4c7b-bc06-70240386b5b4",
                "indicator": {
                    "id": "supertrend",
                    "name": "Supertrend",
                    "category": "Trend",
                    "parameter": {
                        "atrLength": 10,
                        "multiplier": 3,
                        "condition": "Trend Up"
                    },
                    "applyTo": "buy"
                },
                "enabled": True
            },
            {
                "id": "5d62ff02-1c28-47b9-8df8-d50b8ee9af71",
                "indicator": {
                    "id": "rsi",
                    "name": "RSI",
                    "category": "Momentum",
                    "parameter": {
                        "length": 14,
                        "overbought": 70,
                        "oversold": 30,
                        "condition": "Cross Above",
                        "value": 55
                    },
                    "applyTo": "buy"
                },
                "enabled": True
            },
            {
                "id": "4e83db74-f18e-4084-ad10-e0a239dfae7b",
                "indicator": {
                    "id": "adx",
                    "name": "ADX",
                    "category": "Trend",
                    "parameter": {
                        "length": 14,
                        "condition": "ADX >",
                        "value": 25
                    },
                    "applyTo": "buy"
                },
                "enabled": True
            },
            {
                "id": "a7564880-b4fd-47b5-b68a-7414ff6b23ca",
                "indicator": {
                    "id": "vwap",
                    "name": "VWAP",
                    "category": "Volume",
                    "parameter": {
                        "source": "Close",
                        "condition": "Above VWAP"
                    },
                    "applyTo": "buy"
                },
                "enabled": True
            }
        ],
        "sell_conditions": [
            {
                "id": "51ddeb6f-b7b3-4af4-aff1-243a49b5316e",
                "indicator": {
                    "id": "ema",
                    "name": "EMA",
                    "category": "Trend",
                    "parameter": {
                        "fast": 20,
                        "slow": 50,
                        "source": "Close",
                        "condition": "Bearish Cross"
                    },
                    "applyTo": "sell"
                },
                "enabled": True
            },
            {
                "id": "46b9e49d-da0b-4074-97e3-9e5c2b9e1cd0",
                "indicator": {
                    "id": "supertrend",
                    "name": "Supertrend",
                    "category": "Trend",
                    "parameter": {
                        "atrLength": 10,
                        "multiplier": 3,
                        "condition": "Trend Down"
                    },
                    "applyTo": "sell"
                },
                "enabled": True
            },
            {
                "id": "e55a6bd6-9979-482e-adbf-8d18aa13c95c",
                "indicator": {
                    "id": "rsi",
                    "name": "RSI",
                    "category": "Momentum",
                    "parameter": {
                        "length": 14,
                        "overbought": 70,
                        "oversold": 30,
                        "condition": "Cross Below",
                        "value": 45
                    },
                    "applyTo": "sell"
                },
                "enabled": True
            },
            {
                "id": "baf78f26-1e13-490e-9efc-85ca1cdf2c8d",
                "indicator": {
                    "id": "adx",
                    "name": "ADX",
                    "category": "Trend",
                    "parameter": {
                        "length": 14,
                        "condition": "ADX >",
                        "value": 25
                    },
                    "applyTo": "sell"
                },
                "enabled": True
            },
            {
                "id": "7a23832a-236b-4f8f-8855-a9570a7486f4",
                "indicator": {
                    "id": "vwap",
                    "name": "VWAP",
                    "category": "Volume",
                    "parameter": {
                        "source": "Close",
                        "condition": "Above VWAP"
                    },
                    "applyTo": "sell"
                },
                "enabled": True
            }
        ]
    },
    "buy_threshold": 3,
    "sell_threshold": -3,
    "ema_fast": 20,
    "ema_slow": 50,
    "rsi_buy": 40,
    "rsi_sell": 65,
    "tp_percent": 2.0,
    "sl_percent": 1.0,
    "risk_reward": 2,
    "max_open_trades": 3,
    "created_by": "SYSTEM",
    # Published System strategies are visible to traders, but server-side
    # ownership checks keep them read-only for those users.
    "published": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow(),
}

if connected:
    # Migrate the old bootstrap record in place so its existing settings and
    # history are preserved.  Only unowned system records are targeted; no
    # user strategy is converted.
    strategies.update_many(
        {
            "strategy_name": DEFAULT_SYSTEM_STRATEGY_NAME,
            "created_by": "SYSTEM",
            "$or": [
                {"user_id": {"$exists": False}},
                {"user_id": None},
            ],
        },
        {
            "$set": {
                "strategy_type": "System",
                "published": True,
                "updated_at": datetime.utcnow(),
            },
            "$unset": {"user_id": ""},
        },
    )

    # Bootstrap a new database once.  The marker ensures an Admin can delete
    # the template permanently without it being recreated on a later restart.
    if not bootstrap_state.find_one({"key": DEFAULT_SYSTEM_STRATEGY_SEED_MARKER}):
        if strategies.count_documents({}) == 0:
            strategies.insert_one(default_strategy)
            print("Default System Strategy Created")
        bootstrap_state.update_one(
            {"key": DEFAULT_SYSTEM_STRATEGY_SEED_MARKER},
            {"$setOnInsert": {"key": DEFAULT_SYSTEM_STRATEGY_SEED_MARKER, "created_at": datetime.utcnow()}},
            upsert=True,
        )

# ==========================================================
# DEFAULT SETTINGS
# ==========================================================

if connected and settings.count_documents({}) == 0:

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
