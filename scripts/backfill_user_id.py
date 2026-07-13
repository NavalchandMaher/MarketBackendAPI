"""
Backfill missing `user_id` fields for legacy documents.
Sets `user_id` to None for documents that don't have the field yet.
Run: python scripts/backfill_user_id.py
"""
import os
import sys

# Ensure BackendAPI is on sys.path so relative imports work regardless of cwd
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.mongodb import (
    backtest_results,
    paper_trades,
    closed_trades,
    learning_logs,
    notifications,
    settings,
    strategies,
)

collections = [
    ("backtest_results", backtest_results),
    ("paper_trades", paper_trades),
    ("closed_trades", closed_trades),
    ("learning_logs", learning_logs),
    ("notifications", notifications),
    ("settings", settings),
    ("strategies", strategies),
]

if __name__ == "__main__":
    for name, coll in collections:
        missing_count = coll.count_documents({"user_id": {"$exists": False}})
        if missing_count == 0:
            print(f"{name}: no documents to backfill")
            continue
        result = coll.update_many({"user_id": {"$exists": False}}, {"$set": {"user_id": None}})
        print(f"{name}: updated {result.modified_count} documents (set user_id=null)")

    print("Backfill complete. Consider reviewing user-owned records and mapping them appropriately.")
