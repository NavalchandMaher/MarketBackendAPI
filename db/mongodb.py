from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017"
)

db = client["MarketDB"]

paper_trades = db["paper_trades"]
strategies = db["strategies"]
strategy_versions = db["strategy_versions"]
learning_logs = db["learning_logs"]
daily_stats = db["daily_stats"]