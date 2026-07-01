from datetime import datetime
from db.mongodb import (
    paper_trades,
    strategies,
    learning_logs
)

class LearningEngine:

    @staticmethod
    def optimize():

        trades = list(
            paper_trades.find({
                "status": "CLOSED"
            })
        )

        if len(trades) < 100:
            return

        wins = len(
            [x for x in trades if x["profit_loss"] > 0]
        )

        win_rate = wins / len(trades) * 100

        strategy = strategies.find_one(
            {"enabled": True}
        )

        if win_rate < 50:

            strategies.update_one(
                {"_id": strategy["_id"]},
                {
                    "$set": {
                        "buy_threshold":
                            strategy["buy_threshold"] - 1
                    }
                }
            )

            learning_logs.insert_one({
                "action": "OPTIMIZE",
                "win_rate": win_rate,
                "created_at": datetime.utcnow()
            })