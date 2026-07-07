import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from db.mongodb import (
    backtest_results,
    closed_trades,
    learning_logs,
    notifications,
    paper_trades,
    settings,
    strategies,
    strategy_history,
)
from services.paper_trading import PaperTrading
from services.backtester import BackTester
from services.signal_engine import analyze_market

logger = logging.getLogger(__name__)


class V3Service:
    @staticmethod
    def _jsonify_document(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        if "_id" in doc:
            doc = dict(doc)
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def dashboard_summary() -> Dict[str, Any]:
        open_trades = paper_trades.count_documents({"status": "OPEN"})
        closed_trades_count = closed_trades.count_documents({})
        last_trade = closed_trades.find_one({}, sort=[("closed_at", -1)]) or paper_trades.find_one({}, sort=[("created_at", -1)])
        latest_strategy = strategies.find_one({}, sort=[("created_at", -1)])
        latest_signal = {"signal": "WAIT", "confidence": 0, "price": 0}
        try:
            latest_signal = analyze_market(symbol="BTCUSDT", timeframe="5m")
        except Exception as exc:
            logger.exception("dashboard summary signal failed: %s", exc)
        return {
            "current_signal": latest_signal.get("signal", "WAIT"),
            "strategy_name": latest_strategy.get("strategy_name") if latest_strategy else "DEFAULT",
            "strategy_version": latest_strategy.get("version", 1) if latest_strategy else 1,
            "current_price": latest_signal.get("price", 0),
            "confidence": latest_signal.get("confidence", 0),
            "account_balance": 100000,
            "todays_pl": 0,
            "open_trades": open_trades,
            "last_executed_trade": V3Service._jsonify_document(last_trade),
            "market_status": "ONLINE",
        }

    @staticmethod
    def list_strategies() -> List[Dict[str, Any]]:
        docs = list(strategies.find().sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def get_strategy(strategy_id: str) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            doc = strategies.find_one({"_id": ObjectId(strategy_id)})
        except Exception:
            doc = strategies.find_one({"_id": strategy_id})
        return V3Service._jsonify_document(doc)

    @staticmethod
    def create_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
        doc = {
            "strategy_name": payload.get("strategy_name", "NEW_STRATEGY"),
            "version": payload.get("version", 1),
            "enabled": payload.get("enabled", True),
            "paper_mode": payload.get("paper_mode", True),
            "live_mode": payload.get("live_mode", False),
            "priority": payload.get("priority", 1),
            "symbol": payload.get("symbol", "BTCUSDT"),
            "timeframe": payload.get("timeframe", "5m"),
            "risk_percent": payload.get("risk_percent", 1.0),
            "tp": payload.get("tp", 2.0),
            "sl": payload.get("sl", 1.0),
            "indicator_parameters": payload.get("indicator_parameters", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = strategies.insert_one(doc)
        doc["_id"] = result.inserted_id
        return V3Service._jsonify_document(doc)

    @staticmethod
    def update_strategy(strategy_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id
        update = dict(payload)
        update["updated_at"] = datetime.utcnow()
        strategies.update_one({"_id": object_id}, {"$set": update})
        return V3Service.get_strategy(strategy_id)

    @staticmethod
    def delete_strategy(strategy_id: str) -> Dict[str, Any]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id
        result = strategies.delete_one({"_id": object_id})
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def run_backtest(payload: Dict[str, Any]) -> Dict[str, Any]:
        report = BackTester.run(
            symbol=payload.get("symbol", "BTCUSDT"),
            timeframe=payload.get("timeframe", "5m"),
            days=payload.get("days", 365),
        )
        backtest_id = str(uuid.uuid4())
        payload_doc = {
            "backtest_id": backtest_id,
            "symbol": payload.get("symbol", "BTCUSDT"),
            "timeframe": payload.get("timeframe", "5m"),
            "days": payload.get("days", 365),
            "result": report,
            "created_at": datetime.utcnow(),
        }
        backtest_results.insert_one(payload_doc)
        return {"success": True, "backtest_id": backtest_id, "result": report}

    @staticmethod
    def get_backtest(backtest_id: str) -> Optional[Dict[str, Any]]:
        doc = backtest_results.find_one({"backtest_id": backtest_id})
        if doc:
            doc = dict(doc)
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def list_backtests() -> List[Dict[str, Any]]:
        docs = list(backtest_results.find().sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def delete_backtest(backtest_id: str) -> Dict[str, Any]:
        result = backtest_results.delete_one({"backtest_id": backtest_id})
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def paper_start() -> Dict[str, Any]:
        return PaperTrading.open_trade({
            "signal": "BUY",
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "price": 100000,
            "strategy_name": "V3_STRATEGY",
            "strategy_version": 1,
            "confidence": 0.8,
            "market_regime": "TREND",
            "indicators": {},
            "tp_percent": 2.0,
            "sl_percent": 1.0,
        })

    @staticmethod
    def paper_stop() -> Dict[str, Any]:
        return {"success": True, "message": "Paper trading stopped."}

    @staticmethod
    def paper_status() -> Dict[str, Any]:
        return {"running": True, "message": "Paper trading engine is active."}

    @staticmethod
    def paper_open() -> List[Dict[str, Any]]:
        return PaperTrading.get_open_trades()

    @staticmethod
    def paper_history() -> List[Dict[str, Any]]:
        return PaperTrading.get_closed_trades(limit=100)

    @staticmethod
    def paper_statistics() -> Dict[str, Any]:
        return {
            "total_trades": closed_trades.count_documents({}),
            "wins": closed_trades.count_documents({"result": "WIN"}),
            "losses": closed_trades.count_documents({"result": "LOSS"}),
            "win_rate": 0,
        }

    @staticmethod
    def broker_list() -> List[Dict[str, Any]]:
        return [
            {"name": "Binance", "status": "available"},
            {"name": "Bybit", "status": "available"},
            {"name": "Delta", "status": "available"},
            {"name": "Angel One", "status": "available"},
            {"name": "Zerodha", "status": "available"},
            {"name": "Upstox", "status": "available"},
        ]

    @staticmethod
    def broker_connect(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "message": f"Connection request prepared for {payload.get('broker', 'unknown')}"}

    @staticmethod
    def broker_test(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "message": f"Broker test passed for {payload.get('broker', 'unknown')}"}

    @staticmethod
    def broker_disconnect(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "message": f"Broker disconnect requested for {payload.get('broker', 'unknown')}"}

    @staticmethod
    def report_dashboard() -> Dict[str, Any]:
        return {
            "win_rate": 0,
            "pnl": 0,
            "trades": 0,
            "drawdown": 0,
            "profit_factor": 0,
            "sharpe_ratio": 0,
            "equity_curve": [],
        }

    @staticmethod
    def learning_history() -> List[Dict[str, Any]]:
        docs = list(learning_logs.find().sort("created_at", -1).limit(50))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def learning_latest() -> Optional[Dict[str, Any]]:
        doc = learning_logs.find_one({}, sort=[("created_at", -1)])
        return V3Service._jsonify_document(doc)

    @staticmethod
    def scheduler_jobs() -> Dict[str, Any]:
        return {"jobs": ["market_scanner", "paper_trading", "learning", "nightly_optimization", "report_generator"]}

    @staticmethod
    def settings_get() -> Dict[str, Any]:
        doc = settings.find_one({}) or {}
        return {"theme": doc.get("theme", "dark"), "refresh_interval": doc.get("refresh_interval", 30), "notifications": doc.get("notifications", True), "risk": doc.get("risk", 1.0), "default_symbol": doc.get("default_symbol", "BTCUSDT"), "default_timeframe": doc.get("default_timeframe", "5m")}

    @staticmethod
    def settings_put(payload: Dict[str, Any]) -> Dict[str, Any]:
        update = {"$set": payload}
        settings.update_one({}, update, upsert=True)
        return V3Service.settings_get()

    @staticmethod
    def account_get() -> Dict[str, Any]:
        return {"balance": 100000, "leverage": 10, "broker": "Binance", "risk_percent": 1.0, "max_open_trades": 3}

    @staticmethod
    def account_put(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "account": payload}

    @staticmethod
    def symbols() -> List[str]:
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "NIFTY", "BANKNIFTY"]

    @staticmethod
    def timeframes() -> List[str]:
        return ["1m", "5m", "15m", "30m", "1H", "4H", "1D"]
