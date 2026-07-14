import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.mongodb import strategies
from services.v3_service import V3Service


def test_resolve_strategy_payload_uses_saved_strategy_settings():
    strategy_name = "resolved_strategy_test"
    user_id = "user-123"

    try:
        strategies.delete_one({"strategy_name": strategy_name, "user_id": user_id})
        strategies.insert_one(
            {
                "user_id": user_id,
                "strategy_name": strategy_name,
                "version": 2,
                "risk_percent": 1.5,
                "tp": 3.0,
                "sl": 1.25,
                "indicator_parameters": {
                    "buy_conditions": [
                        {
                            "enabled": True,
                            "indicator": {
                                "id": "ema",
                                "parameter": {"fast": 2, "slow": 3, "condition": "Bullish Cross"},
                            },
                        }
                    ],
                    "sell_conditions": [],
                },
            }
        )

        resolved = V3Service._resolve_strategy_payload(
            {"strategy_name": strategy_name},
            user_id=user_id,
        )

        assert resolved["strategy_name"] == strategy_name
        assert resolved["risk_percent"] == 1.5
        assert resolved["tp"] == 3.0
        assert resolved["sl"] == 1.25
        assert resolved["indicator_parameters"]["buy_conditions"][0]["indicator"]["id"] == "ema"
    finally:
        strategies.delete_one({"strategy_name": strategy_name, "user_id": user_id})
