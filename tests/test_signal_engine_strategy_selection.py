import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import signal_engine
from services.v3_service import V3Service
import services.v3_service as v3_service


class FakePaperTrades:
    def find_one(self, query, **_):
        return None

    def count_documents(self, query):
        return 0


def test_analysis_uses_the_users_default_strategy_and_its_parameters(monkeypatch):
    candles = pd.DataFrame({"close": [100.0] * 250})
    enriched = pd.DataFrame(
        {
            "time": range(250),
            "close": [100.0] * 250,
            "ema20": [4.0] * 250,
            "ema50": [3.0] * 250,
            "ema100": [2.0] * 250,
            "ema200": [1.0] * 250,
            "rsi": [50.0] * 250,
            "macd": [1.0] * 250,
            "macd_signal": [0.0] * 250,
            "adx": [10.0] * 250,
            "atr": [1.0] * 250,
            "volume_ratio": [1.0] * 250,
            "bb_upper": [101.0] * 250,
            "bb_lower": [99.0] * 250,
        }
    )
    requested_user_ids = []

    def active_strategy(*, user_id):
        requested_user_ids.append(user_id)
        return {
            "strategy_name": "My default strategy",
            "version": 3,
            "tp": 4.0,
            "sl": 2.0,
            "indicator_parameters": {
                "buy_threshold": 100,
                "sell_threshold": -100,
            },
        }

    monkeypatch.setattr(signal_engine, "get_market_data", lambda *_: candles)
    monkeypatch.setattr(signal_engine, "calculate_indicators", lambda _: enriched)
    monkeypatch.setattr(signal_engine, "get_higher_timeframe", lambda _: "NEUTRAL")
    monkeypatch.setattr(signal_engine, "get_open_interest", lambda *_: (0, 0, 0))
    monkeypatch.setattr(signal_engine, "get_pcr", lambda _: 1.0)
    monkeypatch.setattr(
        signal_engine.MarketRegime, "detect", lambda _: {"regime": "NEUTRAL"}
    )
    monkeypatch.setattr(signal_engine.LearningEngine, "active_strategy", active_strategy)
    monkeypatch.setattr(signal_engine, "paper_trades", FakePaperTrades())

    result = signal_engine.analyze_market("BTCUSDT", "5m", user_id="trader-1")

    assert requested_user_ids == ["trader-1"]
    assert result["signal"] == "WAIT"
    assert result["strategy"] == {
        "name": "My default strategy",
        "version": 3,
        "buy_threshold": 100,
        "sell_threshold": -100,
        "tp_percent": 4.0,
        "sl_percent": 2.0,
    }


def test_dashboard_displays_the_strategy_that_generated_its_signal(monkeypatch):
    monkeypatch.setattr(v3_service, "paper_trades", FakePaperTrades())
    monkeypatch.setattr(v3_service, "closed_trades", FakePaperTrades())
    monkeypatch.setattr(
        v3_service,
        "analyze_market",
        lambda **_: {
            "signal": "BUY",
            "confidence": 82,
            "price": 100.0,
            "strategy": {"name": "My default strategy", "version": 3},
        },
    )

    summary = V3Service.dashboard_summary(user_id="trader-1")

    assert summary["strategy_name"] == "My default strategy"
    assert summary["strategy_version"] == 3
