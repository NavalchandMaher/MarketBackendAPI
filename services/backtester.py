class Backtester:

    @staticmethod
    def run(trades):

        total = len(trades)

        wins = len(
            [t for t in trades if t["profit_loss"] > 0]
        )

        losses = total - wins

        win_rate = (
            wins / total * 100
            if total
            else 0
        )

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate
        }