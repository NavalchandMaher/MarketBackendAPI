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
        latest_signal = {"signal": "WAIT", "confidence": 0, "price": 0}
        try:
            latest_signal = analyze_market(symbol="BTCUSDT", timeframe="5m", user_id=user_id)
        except Exception as exc:
            logger.exception("dashboard summary signal failed: %s", exc)
        signal_strategy = latest_signal.get("strategy") or {}
        return {
            "current_signal": latest_signal.get("signal", "WAIT"),
            # Keep the dashboard label tied to the strategy that generated its
            # signal, rather than the most recently created strategy.
            "strategy_name": signal_strategy.get("name", "DEFAULT"),
            "strategy_version": signal_strategy.get("version", 1),
            "current_price": latest_signal.get("price", 0),
            "confidence": latest_signal.get("confidence", 0),
            "account_balance": 100000,
            "todays_pl": 0,
            "open_trades": open_trades,
            "last_executed_trade": V3Service._jsonify_document(last_trade),
            "market_status": "ONLINE",
        }

    @staticmethod
    def list_strategies(user_id: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        # For non-admin users, only include System strategies that are published
        if user_id:
            if str(role).lower() == "admin":
                query = {"$or": [{"user_id": user_id}, {"strategy_type": "System"}]}
            else:
                query = {
                    "$or": [
                        {"user_id": user_id},
                        {"$and": [{"strategy_type": "System"}, {"published": True}]},
                    ]
                }
        else:
            # No user scoping — return all (admins calling without user_id)
            query = {}
        docs = list(strategies.find(query).sort("created_at", -1))
        result = [V3Service._jsonify_document(doc) for doc in docs]

        # A trader may select a published System strategy as their own default
        # without mutating the global System strategy for every other user.
        if user_id and str(role).lower() != "admin":
            preference = settings.find_one({"user_id": user_id}) or {}
            default_strategy_id = preference.get("default_strategy_id")
            if default_strategy_id:
                for strategy in result:
                    strategy["is_default"] = strategy.get("id") == default_strategy_id

        return result

    @staticmethod
    def list_all_strategies() -> List[Dict[str, Any]]:
        docs = list(strategies.find({}).sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def get_strategy(strategy_id: str, user_id: Optional[str] = None, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id

        if user_id:
            if str(role).lower() == "admin":
                query = {
                    "_id": object_id,
                    "$or": [{"user_id": user_id}, {"strategy_type": "System"}],
                }
            else:
                # Non-admins may only see their own strategies or published System strategies
                query = {
                    "_id": object_id,
                    "$or": [
                        {"user_id": user_id},
                        {"$and": [{"strategy_type": "System"}, {"published": True}]},
                    ],
                }
        else:
            query = {"_id": object_id}

        doc = strategies.find_one(query)
        return V3Service._jsonify_document(doc)

    @staticmethod
    def create_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = payload.get("user_id")
        if payload.get("is_default"):
            if user_id:
                strategies.update_many(
                    {"user_id": user_id, "is_default": True},
                    {"$set": {"is_default": False}},
                )
                settings.update_one(
                    {"user_id": user_id},
                    {"$unset": {"default_strategy_id": ""}},
                )
            elif payload.get("strategy_type") == "System":
                strategies.update_many(
                    {"strategy_type": "System", "is_default": True},
                    {"$set": {"is_default": False}},
                )

        doc = {
            "user_id": user_id,
            "strategy_name": payload.get("strategy_name", "NEW_STRATEGY"),
            "version": payload.get("version", 1),
            "enabled": payload.get("enabled", True),
            "paper_mode": payload.get("paper_mode", True),
            "live_mode": payload.get("live_mode", False),
            "priority": payload.get("priority", 1),
            "symbol": payload.get("symbol", "BTCUSDT"),
            "timeframe": payload.get("timeframe", "5m"),
            "strategy_type": payload.get("strategy_type", "Scalping"),
            "risk_percent": payload.get("risk_percent", 1.0),
            "tp": payload.get("tp", 2.0),
            "sl": payload.get("sl", 1.0),
            "is_default": payload.get("is_default", False),
            "indicator_parameters": payload.get("indicator_parameters", {}),
            "created_by": payload.get("created_by", "TRADER"),
            # Persist published flag so system strategies visibility works as intended
            "published": bool(payload.get("published", False)),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = strategies.insert_one(doc)
        doc["_id"] = result.inserted_id
        return V3Service._jsonify_document(doc)

    @staticmethod
    def update_strategy(strategy_id: str, payload: Dict[str, Any], user_id: Optional[str] = None, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(strategy_id)
        except Exception:
            object_id = strategy_id

        existing = strategies.find_one({"_id": object_id})
        if not existing:
            return None

        if payload.get("is_default"):
            if existing.get("strategy_type") == "System":
                strategies.update_many(
                    {"strategy_type": "System", "is_default": True, "_id": {"$ne": object_id}},
                    {"$set": {"is_default": False}},
                )
            elif user_id:
                strategies.update_many(
                    {"user_id": user_id, "is_default": True, "_id": {"$ne": object_id}},
                    {"$set": {"is_default": False}},
                )
                settings.update_one(
                    {"user_id": user_id},
                    {"$unset": {"default_strategy_id": ""}},
                )

        update = dict(payload)
        update["updated_at"] = datetime.utcnow()

        # Prevent lowering created_by for existing system strategies unless explicitly provided by Admin logic.
        if existing.get("strategy_type") == "System" and "created_by" not in update:
            update["created_by"] = existing.get("created_by", "SYSTEM")

        is_system = str(existing.get("strategy_type", "")).lower() == "system"
        if is_system:
            if str(role).lower() != "admin":
                return None
            query = {"_id": object_id, "strategy_type": "System"}
        else:
            if not user_id or existing.get("user_id") != user_id:
                return None
            query = {"_id": object_id, "user_id": user_id}

        result = strategies.update_one(query, {"$set": update})
        if result.matched_count == 0:
            return None
        return V3Service.get_strategy(strategy_id, user_id=user_id, role=role)

    @staticmethod
    def set_user_default_system_strategy(
        strategy_id: str, user_id: str, strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist a trader's System-strategy preference without editing it."""
        settings.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "default_strategy_id": strategy_id,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        result = V3Service._jsonify_document(strategy) or {}
        result["is_default"] = True
        return result

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
    def _resolve_strategy_payload(payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        resolved = dict(payload)

        strategy_name = resolved.get("strategy_name")
        if not strategy_name:
            return resolved

        query = {"strategy_name": strategy_name}
        if user_id:
            query["user_id"] = user_id

        strategy_doc = strategies.find_one(query)
        if not strategy_doc:
            return resolved

        for key in ["risk_percent", "tp", "sl", "symbol", "timeframe", "enabled", "paper_mode", "live_mode", "version", "priority"]:
            if key in strategy_doc and resolved.get(key) in (None, ""):
                resolved[key] = strategy_doc.get(key)

        if not resolved.get("indicator_parameters"):
            resolved["indicator_parameters"] = strategy_doc.get("indicator_parameters", {}) or {}
        elif isinstance(resolved.get("indicator_parameters"), dict) and isinstance(strategy_doc.get("indicator_parameters"), dict):
            merged = dict(strategy_doc.get("indicator_parameters", {}))
            merged.update(resolved["indicator_parameters"])
            resolved["indicator_parameters"] = merged

        if resolved.get("strategy_name") in {None, ""}:
            resolved["strategy_name"] = strategy_doc.get("strategy_name")

        return resolved

    @staticmethod
    def run_backtest(
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        backtest_id: Optional[str] = None,
        create_record: bool = True,
    ) -> Dict[str, Any]:
        if payload.get("start_date") and payload.get("end_date"):
            try:
                start = datetime.fromisoformat(payload["start_date"])
                end = datetime.fromisoformat(payload["end_date"])
                payload["days"] = max(1, (end - start).days)
            except Exception:
                pass

        try:
            resolved_payload = V3Service._resolve_strategy_payload(payload, user_id=user_id)

            # If a full strategy payload was provided (indicator parameters or strategy_name),
            # run the backtest for that single strategy. Otherwise run the dashboard (all strategies).
            if resolved_payload.get("indicator_parameters") or resolved_payload.get("strategy_name"):
                # Load and prepare history
                df = BackTester.load_history(
                    resolved_payload.get("symbol", "BTCUSDT"),
                    resolved_payload.get("timeframe", "5m"),
                    resolved_payload.get("days", 365),
                )
                df = BackTester.prepare(df)

                # Construct a strategy payload that preserves the new UI condition structure.
                ind_params = resolved_payload.get("indicator_parameters", {}) or {}
                if not isinstance(ind_params, dict):
                    ind_params = {}

                strategy_def = {
                    "strategy_name": resolved_payload.get("strategy_name"),
                    "version": resolved_payload.get("version", 1),
                    "tp_percent": resolved_payload.get("tp", 2.0),
                    "sl_percent": resolved_payload.get("sl", 1.0),
                    "buy_threshold": resolved_payload.get("buy_threshold", 3),
                    "sell_threshold": resolved_payload.get("sell_threshold", -3),
                    "buy_conditions": ind_params.get("buy_conditions", []),
                    "sell_conditions": ind_params.get("sell_conditions", []),
                }

                # Keep the legacy flat fields populated when simple RSI odds are present.
                if isinstance(ind_params, dict):
                    for cond in ind_params.get("buy_conditions", []):
                        indicator = cond.get("indicator", {})
                        if indicator.get("id") == "rsi":
                            params = indicator.get("parameter", {}) or {}
                            strategy_def["rsi_buy"] = params.get("value") or params.get("oversold") or params.get("length")
                            strategy_def["rsi_sell"] = params.get("overbought")
                            break

                # Run the single-strategy backtest
                trades = BackTester.run_strategy(df, strategy_def)
                single_report = BackTester.report(trades)
                single_report["strategy_name"] = strategy_def.get("strategy_name") or "PAYLOAD_STRATEGY"
                single_report["strategy_version"] = strategy_def.get("version", 1)
                single_report["symbol"] = resolved_payload.get("symbol", "BTCUSDT")
                single_report["timeframe"] = resolved_payload.get("timeframe", "5m")
                single_report["days"] = resolved_payload.get("days", 365)

                report = single_report
            else:
                report = BackTester.run(
                    symbol=resolved_payload.get("symbol", "BTCUSDT"),
                    timeframe=resolved_payload.get("timeframe", "5m"),
                    days=resolved_payload.get("days", 365),
                    user_id=user_id,
                )
        except Exception as exc:
            raise RuntimeError(f"BackTester.run failed: {exc}") from exc

        if create_record:
            payload_doc = {
                "user_id": user_id or payload.get("user_id"),
                "strategy_name": payload.get("strategy_name"),
                "symbol": payload.get("symbol", "BTCUSDT"),
                "timeframe": payload.get("timeframe", "5m"),
                "days": payload.get("days", 365),
                "start_date": payload.get("start_date"),
                "end_date": payload.get("end_date"),
                "initial_capital": payload.get("initial_capital", 100000.0),
                "commission": payload.get("commission", 0.0),
                "slippage": payload.get("slippage", 0.0),
                "date_range": payload.get("date_range"),
                "result": report,
                "status": payload.get("status", "completed"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            result = backtest_results.insert_one(payload_doc)
            inserted_id = str(result.inserted_id)
            return {"success": True, "backtest_id": inserted_id, "result": report}

        return {"success": True, "backtest_id": str(uuid.uuid4()), "result": report}

    @staticmethod
    def get_backtest(backtest_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(backtest_id)
        except Exception:
            object_id = backtest_id
        query = {"_id": object_id, **V3Service._build_user_scope(user_id)}
        doc = backtest_results.find_one(query)
        return V3Service._jsonify_document(doc)

    @staticmethod
    def list_backtests(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Return only user-specific backtests; do not include system backtests
        query = V3Service._build_user_scope(user_id)
        docs = list(backtest_results.find(query).sort("created_at", -1))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def delete_backtest(backtest_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        from bson.objectid import ObjectId
        try:
            object_id = ObjectId(backtest_id)
        except Exception:
            object_id = backtest_id
        result = backtest_results.delete_one({"_id": object_id, **V3Service._build_user_scope(user_id)})
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def paper_start(
        user_id: Optional[str] = None,
        symbol: str = "BTCUSDT",
        timeframe: str = "5m",
    ) -> Dict[str, Any]:
        """Open a paper trade using a fresh signal from the user's default strategy."""
        analysis = analyze_market(symbol=symbol, timeframe=timeframe, user_id=user_id)
        if analysis.get("error"):
            return {"success": False, "message": analysis["error"]}
        if analysis.get("signal") == "WAIT":
            return {
                "success": False,
                "message": "WAIT signal. Trade not opened.",
                "analysis": analysis,
            }

        strategy = analysis.get("strategy") or {}
        return PaperTrading.open_trade({
            "user_id": user_id,
            "signal": analysis.get("signal", "WAIT"),
            "symbol": analysis.get("symbol", symbol),
            "timeframe": analysis.get("timeframe", timeframe),
            "price": analysis.get("price", 0),
            "strategy_name": strategy.get("name", "DEFAULT"),
            "strategy_version": strategy.get("version", 1),
            "confidence": analysis.get("confidence", 0),
            "market_regime": analysis.get("market_regime", "UNKNOWN"),
            "indicators": analysis.get("indicators", {}),
            "tp_percent": strategy.get("tp_percent", 2.0),
            "sl_percent": strategy.get("sl_percent", 1.0),
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
        total_trades = closed_trades.count_documents(query)
        wins = closed_trades.count_documents({"result": "WIN", **query})
        losses = closed_trades.count_documents({"result": "LOSS", **query})
        win_rate = round((wins / total_trades * 100), 2) if total_trades > 0 else 0
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
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
    def learning_history(
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = V3Service._build_user_scope(user_id)
        if category:
            query["category"] = category
        if days:
            query["created_at"] = {"$gte": datetime.utcnow() - timedelta(days=days)}
        docs = list(learning_logs.find(query).sort("created_at", -1).limit(50))
        return [V3Service._jsonify_document(doc) for doc in docs]

    @staticmethod
    def learning_latest(user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        doc = learning_logs.find_one(V3Service._build_user_scope(user_id), sort=[("created_at", -1)])
        return V3Service._jsonify_document(doc)

    @staticmethod
    def get_learning_log(
        log_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId

        try:
            object_id = ObjectId(log_id)
        except Exception:
            object_id = log_id
        doc = learning_logs.find_one(
            {"_id": object_id, **V3Service._build_user_scope(user_id)}
        )
        return V3Service._jsonify_document(doc)

    @staticmethod
    def create_learning_log(
        payload: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "title": payload["title"].strip(),
            "description": payload["description"].strip(),
            "category": payload.get("category", "lesson").strip(),
            "metadata": payload.get("metadata", {}),
            "source": "manual",
            "created_at": now,
            "updated_at": now,
        }
        result = learning_logs.insert_one(doc)
        doc["_id"] = result.inserted_id
        return V3Service._jsonify_document(doc)

    @staticmethod
    def update_learning_log(
        log_id: str, payload: Dict[str, Any], user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        from bson.objectid import ObjectId

        try:
            object_id = ObjectId(log_id)
        except Exception:
            object_id = log_id
        update = {
            "title": payload["title"].strip(),
            "description": payload["description"].strip(),
            "category": payload.get("category", "lesson").strip(),
            "metadata": payload.get("metadata", {}),
            "updated_at": datetime.utcnow(),
        }
        result = learning_logs.update_one(
            {"_id": object_id, **V3Service._build_user_scope(user_id)},
            {"$set": update},
        )
        if result.matched_count == 0:
            return None
        return V3Service.get_learning_log(log_id, user_id=user_id)

    @staticmethod
    def delete_learning_log(
        log_id: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        from bson.objectid import ObjectId

        try:
            object_id = ObjectId(log_id)
        except Exception:
            object_id = log_id
        result = learning_logs.delete_one(
            {"_id": object_id, **V3Service._build_user_scope(user_id)}
        )
        return {"success": result.deleted_count > 0, "deleted": result.deleted_count > 0}

    @staticmethod
    def scheduler_jobs(user_id: Optional[str] = None) -> Dict[str, Any]:
        # Return the list of scheduler jobs. User_id is accepted for
        # future per-user job scoping but currently not applied.
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
