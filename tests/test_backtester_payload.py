import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.backtester import BackTester


def test_execute_strategy_supports_new_ui_buy_conditions():
    df = pd.DataFrame(
        {
            "close": [10, 11, 12, 14, 16],
            "high": [10, 12, 13, 15, 17],
            "low": [9, 10, 11, 13, 15],
            "open": [10, 10, 12, 13, 15],
            "volume": [100, 110, 120, 130, 140],
        }
    )

    strategy = {
        "buy_conditions": [
            {
                "indicator": {
                    "id": "ema",
                    "parameter": {"fast": 2, "slow": 3, "condition": "Bullish Cross"},
                }
            }
        ],
        "sell_conditions": [],
    }

    # build a history slice that includes enough rows for the indicator calculation
    history = df.copy()

    assert BackTester.execute_strategy(history, strategy) == "BUY"
