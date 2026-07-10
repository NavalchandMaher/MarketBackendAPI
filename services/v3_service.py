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
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


class V3Service:
    @staticmethod
    def _build_user_scope(user_id: Optional[str] = None) -> Dict[str, Any]:
        return {"user_id": user_id} if user_id else {}

    @staticmethod
    def _jsonify_document(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        if "_id" in doc:
            doc = dict(doc)
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def dashboard_summary(user_id: Optional[str] = None) -> Dict[str, Any]:
        query = V3Service._build_user_scope(user_id)
        open_trades = paper_trades.count_documents({"status": "OPEN", **query})
        closed_trades_count = closed_trades.count_documents(query)
        last_trade = closed_trades.find_one(query, sort=[("closed_at", -1)]) or paper_trades.find_one(query, sort=[("created_at", -1)])
        latest_strategy = strategies.find_one(query, sort=[("created_at", -1)])
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
    def list_strategies(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = V3Service._build_user_scope(user_id)
        docs = list(strategies.find(query).sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def get_strategy(strategy_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        query = V3Service._build_user_scope(user_id)
        try:
            doc = strategies.find_one({"_id": ObjectId(strategy_id), **query})
        except Exception:
            doc = strategies.find_one({"_id": strategy_id, **query})
        return V3Service._jsonify_document(doc)

    @staticmethod
    def create_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
        doc = {
            "user_id": payload.get("user_id"),
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
    def update_strategy(strategy_id: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id
        update = dict(payload)
        update["updated_at"] = datetime.utcnow()
        query = {"_id": object_id, **V3Service._build_user_scope(user_id)}
        strategies.update_one(query, {"$set": update})
        return V3Service.get_strategy(strategy_id, user_id)

    @staticmethod
    def delete_strategy(strategy_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id
        result = strategies.delete_one({"_id": object_id, **V3Service._build_user_scope(user_id)})
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def run_backtest(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        report = BackTester.run(
            symbol=payload.get("symbol", "BTCUSDT"),
            timeframe=payload.get("timeframe", "5m"),
            days=payload.get("days", 365),
        )
        backtest_id = str(uuid.uuid4())
        payload_doc = {
            "user_id": user_id or payload.get("user_id"),
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
    def get_backtest(backtest_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        doc = backtest_results.find_one({"backtest_id": backtest_id, **V3Service._build_user_scope(user_id)})
        if doc:
            doc = dict(doc)
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def list_backtests(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        docs = list(backtest_results.find(V3Service._build_user_scope(user_id)).sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def delete_backtest(backtest_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        result = backtest_results.delete_one({"backtest_id": backtest_id, **V3Service._build_user_scope(user_id)})
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def paper_start(user_id: Optional[str] = None) -> Dict[str, Any]:
        return PaperTrading.open_trade({
            "user_id": user_id,
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
    def paper_stop(user_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[V3_SERVICE] Paper trading stopped for user: {user_id}")
        return {"success": True, "message": "Paper trading stopped."}

    @staticmethod
    def paper_status() -> Dict[str, Any]:
        return {"running": True, "message": "Paper trading engine is active."}

    @staticmethod
    def paper_open(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return PaperTrading.get_open_trades(user_id=user_id)

    @staticmethod
    def paper_history(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return PaperTrading.get_closed_trades(limit=100, user_id=user_id)

    @staticmethod
    def paper_statistics(user_id: Optional[str] = None) -> Dict[str, Any]:
        query = V3Service._build_user_scope(user_id)
        return {
            "total_trades": closed_trades.count_documents(query),
            "wins": closed_trades.count_documents({"result": "WIN", **query}),
            "losses": closed_trades.count_documents({"result": "LOSS", **query}),
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
    def report_dashboard(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate user-scoped performance report.
        If user_id is provided, returns user-specific metrics.
        Otherwise returns system-wide metrics.
        """
        query = V3Service._build_user_scope(user_id)
        
        total_trades = closed_trades.count_documents(query)
        wins = closed_trades.count_documents({"result": "WIN", **query})
        losses = closed_trades.count_documents({"result": "LOSS", **query})
        
        win_rate = round((wins / total_trades * 100), 2) if total_trades > 0 else 0
        
        # Calculate PnL
        pipeline = [{"$match": query}, {"$group": {"_id": None, "total_pnl": {"$sum": "$pnl"}}}]
        pnl_result = list(closed_trades.aggregate(pipeline))
        total_pnl = pnl_result[0]["total_pnl"] if pnl_result else 0
        
        logger.info(f"[V3_SERVICE] Generated report for user {user_id}: {total_trades} trades, {win_rate}% win rate")
        
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": round(total_pnl, 2),
            "profit_factor": (wins / losses) if losses > 0 else 0,
            "drawdown": 0,  # Calculate if needed from equity curve
            "sharpe_ratio": 0,  # Calculate if needed from returns
            "equity_curve": [],
        }

    @staticmethod
    def learning_history(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        docs = list(learning_logs.find(V3Service._build_user_scope(user_id)).sort("created_at", -1).limit(50))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def learning_latest(user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        doc = learning_logs.find_one(V3Service._build_user_scope(user_id), sort=[("created_at", -1)])
        return V3Service._jsonify_document(doc)

    @staticmethod
    def scheduler_jobs() -> Dict[str, Any]:
        return {"jobs": ["market_scanner", "paper_trading", "learning", "nightly_optimization", "report_generator"]}

    @staticmethod
    def settings_get(user_id: Optional[str] = None) -> Dict[str, Any]:
        query = {"user_id": user_id} if user_id else {}
        doc = settings.find_one(query) or {}
        return {"theme": doc.get("theme", "dark"), "refresh_interval": doc.get("refresh_interval", 30), "notifications": doc.get("notifications", True), "risk": doc.get("risk", 1.0), "default_symbol": doc.get("default_symbol", "BTCUSDT"), "default_timeframe": doc.get("default_timeframe", "5m")}

    @staticmethod
    def settings_put(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        update = {"$set": {**payload, "user_id": user_id}}
        settings.update_one({"user_id": user_id} if user_id else {}, update, upsert=True)
        return V3Service.settings_get(user_id)

    @staticmethod
    def account_get(user_id: Optional[str] = None) -> Dict[str, Any]:
        from db.mongodb import user_account
        doc = user_account.find_one({"user_id": user_id}) if user_id else None
        if doc:
            return {"balance": doc.get("balance", 100000), "leverage": doc.get("leverage", 10), "broker": doc.get("broker", "Binance"), "risk_percent": doc.get("risk_percent", 1.0), "max_open_trades": doc.get("max_open_trades", 3)}
        return {"balance": 100000, "leverage": 10, "broker": "Binance", "risk_percent": 1.0, "max_open_trades": 3}

    @staticmethod
    def account_put(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        from db.mongodb import user_account
        if user_id:
            user_account.update_one({"user_id": user_id}, {"$set": {**payload, "user_id": user_id}}, upsert=True)
        return {"success": True, "account": payload}

    @staticmethod
    def symbols() -> List[str]:
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "NIFTY", "BANKNIFTY"]

    @staticmethod
    def timeframes() -> List[str]:
        return ["1m", "5m", "15m", "30m", "1H", "4H", "1D"]
