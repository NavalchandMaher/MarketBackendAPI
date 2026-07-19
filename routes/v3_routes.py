from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from typing import Any, Dict, Optional
import uuid
from datetime import datetime
import traceback

from db.mongodb import backtest_results, notifications

from services.v3_service import V3Service
from services.auth_service import AuthService
from services.signal_engine import analyze_market
from services.scheduler_service import SchedulerService

router = APIRouter(prefix="/v3", tags=["v3"])


class StrategyPayload(BaseModel):
    # Updates are partial (for example, setting a strategy as default only
    # sends `is_default`), so the route validates the name only on creation.
    strategy_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[int] = 1
    enabled: Optional[bool] = True
    paper_mode: Optional[bool] = True
    live_mode: Optional[bool] = False
    priority: Optional[int] = 1
    exchange: Optional[str] = "BINANCE"
    symbol: Optional[str] = "BTCUSDT"
    timeframe: Optional[str] = "5m"
    strategy_type: Optional[str] = "Scalping"
    risk_percent: Optional[float] = 1.0
    tp: Optional[float] = 2.0
    sl: Optional[float] = 1.0
    is_default: Optional[bool] = False
    published: Optional[bool] = False

    indicator_parameters: Dict[str, Any] = Field(default_factory=dict)


class BacktestPayload(BaseModel):
    strategy_name: Optional[str] = None
    symbol: Optional[str] = "BTCUSDT"
    timeframe: Optional[str] = "5m"
    days: Optional[int] = 365
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: Optional[float] = 100000.0
    commission: Optional[float] = 0.0
    slippage: Optional[float] = 0.0
    date_range: Optional[Dict[str, str]] = None


class PublishPayload(BaseModel):
    published: bool = False


class BrokerPayload(BaseModel):
    broker: Optional[str] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None


class SettingsPayload(BaseModel):
    theme: Optional[str] = None
    refresh_interval: Optional[int] = None
    notifications: Optional[bool] = None
    risk: Optional[float] = None
    default_symbol: Optional[str] = None
    default_timeframe: Optional[str] = None


class AccountPayload(BaseModel):
    balance: Optional[float] = None
    leverage: Optional[int] = None
    broker: Optional[str] = None
    risk_percent: Optional[float] = None
    max_open_trades: Optional[int] = None


class LearningLogPayload(BaseModel):
    """A user-authored note shown in the Learning Logs screen."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    category: str = Field(default="lesson", min_length=1, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("/dashboard")
def dashboard(user=Depends(AuthService.get_current_user)):
    return V3Service.dashboard_summary(user_id=str(user["_id"]))


@router.get("/analysis")
def analysis(symbol: str = Query("BTCUSDT"), timeframe: str = Query("5m"), user=Depends(AuthService.get_current_user)):
    """Market analysis endpoint - requires authentication"""
    return analyze_market(symbol, timeframe, user_id=str(user["_id"]))


@router.get("/strategies")
def strategies_list(user=Depends(AuthService.get_current_user)):
    # Only return published System strategies to non-admin users
    return V3Service.list_strategies(user_id=str(user["_id"]), role=user.get("role"))


@router.get("/strategies/{strategy_id}")
def strategy_detail(strategy_id: str, user=Depends(AuthService.get_current_user)):
    strategy = V3Service.get_strategy(strategy_id, user_id=str(user["_id"]), role=user.get("role"))
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.get("/admin/strategies")
def admin_list_strategies(user=Depends(AuthService.require_role("Admin"))):
    return V3Service.list_all_strategies()


@router.put("/strategies/{strategy_id}/publish")
def publish_strategy(
    strategy_id: str,
    payload: PublishPayload,
    user=Depends(AuthService.require_role("Admin")),
):
    existing_strategy = V3Service.get_strategy(strategy_id, user_id=str(user["_id"]), role=user.get("role"))
    if not existing_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if existing_strategy.get("strategy_type") != "System":
        raise HTTPException(status_code=403, detail="Only system strategies can be published")

    updated = V3Service.update_strategy(
        strategy_id,
        {"published": payload.published},
        user_id=str(user["_id"]),
        role=user.get("role"),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return updated


@router.post("/strategies", status_code=201)
def create_strategy(payload: StrategyPayload, user=Depends(AuthService.get_current_user)):
    data = payload.model_dump(exclude_none=True)
    strategy_name = data.get("strategy_name", "").strip()
    if not strategy_name:
        raise HTTPException(status_code=422, detail="Strategy name is required")
    data["strategy_name"] = strategy_name
    # Determine creator type from user role
    role = user.get("role", "Trader")
    created_by = "SYSTEM" if str(role).lower() == "admin" else "TRADER"

    # Enforce admin-only creation for System strategies
    if data.get("strategy_type") == "System":
        if str(role).lower() != "admin":
            raise HTTPException(status_code=403, detail="Only admins can create system strategies")
        # System strategies are global — do not attach a user_id
        data.pop("user_id", None)
        # Admin may set published flag; default False
        data["published"] = bool(data.get("published", False))
    else:
        # User-scoped strategy
        data["user_id"] = str(user["_id"])
        # Non-system strategies are not published to all users
        # and published is not required for trader-owned strategies.
        data.pop("published", None)

    # Always record who created the strategy based on the actor's role
    data["created_by"] = created_by

    try:
        return V3Service.create_strategy(data)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="A strategy with this name already exists for this owner",
        )


@router.put("/strategies/{strategy_id}")
def update_strategy(strategy_id: str, payload: StrategyPayload, user=Depends(AuthService.get_current_user)):
    # Fetch existing strategy with role-aware visibility
    existing_strategy = V3Service.get_strategy(strategy_id, user_id=str(user["_id"]), role=user.get("role"))
    if not existing_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if existing_strategy.get("strategy_type") == "System" and user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can update system strategies")

    # Only apply fields sent by the client.  In particular, controls such as
    # "Set as default" submit only `is_default` and must not reset the other
    # strategy fields to their model defaults.
    data = payload.model_dump(exclude_unset=True)
    if data.get("strategy_type") == "System" and user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can change strategy type to System")

    # Ensure created_by reflects the updater's role when creating/changing ownership
    role = user.get("role", "Trader")
    existing_is_system = existing_strategy.get("strategy_type") == "System"
    requested_is_system = data.get("strategy_type", existing_strategy.get("strategy_type")) == "System"
    if requested_is_system:
        data.setdefault("created_by", "SYSTEM")
        # Only Admins may change the published flag
        if "published" in data and str(role).lower() != "admin":
            raise HTTPException(status_code=403, detail="Only admins can change published state for System strategies")
        # A newly converted System strategy is private until an Admin publishes it.
        if not existing_is_system:
            data.setdefault("published", False)
    elif "strategy_type" in data:
        # Explicitly converting a System strategy to a user strategy removes its
        # global publication state.  Partial updates leave it untouched.
        data.setdefault("created_by", "SYSTEM" if str(role).lower() == "admin" else "TRADER")
        data["published"] = False

    updated = V3Service.update_strategy(strategy_id, data, user_id=str(user["_id"]), role=user.get("role"))
    if not updated:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return updated


@router.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: str, user=Depends(AuthService.get_current_user)):
    existing_strategy = V3Service.get_strategy(strategy_id, user_id=str(user["_id"]))
    if not existing_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if existing_strategy.get("strategy_type") == "System" and user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can delete system strategies")

    if existing_strategy.get("strategy_type") == "System":
        return V3Service.delete_strategy(strategy_id, user_id=None)

    return V3Service.delete_strategy(strategy_id, user_id=str(user["_id"]))


@router.post("/backtest/run")
def run_backtest(payload: BacktestPayload, user=Depends(AuthService.get_current_user)):
    """Synchronous backtest run (blocking) - kept for compatibility."""
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    result = V3Service.run_backtest(data)
    return result


async def _run_backtest_background(data: Dict[str, Any], backtest_id: str, user_id: str):
    """Background task: run the backtest and update the DB and notifications."""
    from bson.objectid import ObjectId
    try:
        # Convert backtest_id to ObjectId for database operations
        try:
            object_id = ObjectId(backtest_id)
        except Exception:
            object_id = backtest_id

        # Delegate to the existing service (blocking) inside threadpool
        import asyncio
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, V3Service.run_backtest, data, user_id, backtest_id, False)

        # Update the backtest record with result and completed status
        backtest_results.update_one(
            {"_id": object_id, "user_id": user_id},
            {
                "$set": {
                    "result": result.get("result"),
                    "status": "completed",
                    "updated_at": datetime.utcnow(),
                    "backtest_response": result,
                }
            },
        )

        # Insert a notification for the user
        try:
            notifications.insert_one(
                {
                    "user_id": user_id,
                    "type": "backtest_completed",
                    "backtest_id": backtest_id,
                    "created_at": datetime.utcnow(),
                    "read": False,
                }
            )
        except Exception:
            # best-effort: do not crash background worker on notification failure
            pass
    except Exception as exc:
        error_message = str(exc)
        stack_trace = traceback.format_exc()
        try:
            object_id = ObjectId(backtest_id)
        except Exception:
            object_id = backtest_id
        backtest_results.update_one(
            {"_id": object_id, "user_id": user_id},
            {
                "$set": {
                    "status": "failed",
                    "updated_at": datetime.utcnow(),
                    "error_message": error_message,
                    "error_trace": stack_trace,
                }
            },
        )


@router.post("/backtest/async")
def run_backtest_async(
    payload: BacktestPayload,
    background_tasks: BackgroundTasks,
    user=Depends(AuthService.get_current_user),
):
    """Start a backtest asynchronously and return immediately with a backtest_id."""
    data = payload.model_dump(exclude_none=True)
    user_id = str(user["_id"])

    # Insert a running record so clients can poll status
    record = {
        "user_id": user_id,
        "strategy_name": data.get("strategy_name"),
        "symbol": data.get("symbol", "BTCUSDT"),
        "timeframe": data.get("timeframe", "5m"),
        "days": data.get("days", 365),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "initial_capital": data.get("initial_capital", 100000.0),
        "commission": data.get("commission", 0.0),
        "slippage": data.get("slippage", 0.0),
        "date_range": data.get("date_range"),
        "status": "running",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    try:
        result = backtest_results.insert_one(record)
        backtest_id = str(result.inserted_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create backtest record")

    background_tasks.add_task(_run_backtest_background, data, backtest_id, user_id)

    return {"success": True, "backtest_id": backtest_id, "status": "started"}


@router.get("/backtest/history")
def list_backtests(user=Depends(AuthService.get_current_user)):
    user_id = str(user["_id"])
    return V3Service.list_backtests(user_id=user_id)


@router.get("/backtest/{backtest_id}")
def get_backtest(backtest_id: str, user=Depends(AuthService.get_current_user)):
    backtest = V3Service.get_backtest(backtest_id, user_id=str(user["_id"]))
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtest


@router.get("/backtest/{backtest_id}/status")
def backtest_status(backtest_id: str, user=Depends(AuthService.get_current_user)):
    from bson.objectid import ObjectId
    try:
        object_id = ObjectId(backtest_id)
    except Exception:
        object_id = backtest_id
    
    query = {"_id": object_id, "user_id": str(user["_id"])}
    doc = backtest_results.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {
        "backtest_id": str(doc["_id"]),
        "status": doc.get("status", "unknown"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@router.delete("/backtest/{backtest_id}")
def delete_backtest(backtest_id: str, user=Depends(AuthService.get_current_user)):
    return V3Service.delete_backtest(backtest_id, user_id=str(user["_id"]))


@router.post("/paper/start")
def paper_start(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_start(user_id=str(user["_id"]))


@router.post("/paper/stop")
def paper_stop(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_stop(user_id=str(user["_id"]))


@router.get("/paper/status")
def paper_status(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_status()


@router.get("/paper/open")
def paper_open(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_open(user_id=str(user["_id"]))


@router.get("/paper/history")
def paper_history(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_history(user_id=str(user["_id"]))


@router.get("/paper/statistics")
def paper_statistics(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_statistics(user_id=str(user["_id"]))


@router.get("/brokers")
def brokers():
    return V3Service.broker_list()


@router.post("/broker/connect")
def broker_connect(payload: BrokerPayload, user=Depends(AuthService.get_current_user)):
    """Connect broker credentials for current user"""
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    return V3Service.broker_connect(data)


@router.post("/broker/test")
def broker_test(payload: BrokerPayload, user=Depends(AuthService.get_current_user)):
    """Test broker connection for current user"""
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    return V3Service.broker_test(data)


@router.post("/broker/disconnect")
def broker_disconnect(payload: BrokerPayload, user=Depends(AuthService.get_current_user)):
    """Disconnect broker for current user"""
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    return V3Service.broker_disconnect(data)


@router.get("/reports/dashboard")
def reports_dashboard(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/reports/daily")
def reports_daily(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/reports/monthly")
def reports_monthly(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/reports/yearly")
def reports_yearly(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/reports/equity")
def reports_equity(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/reports/performance")
def reports_performance(user=Depends(AuthService.get_current_user)):
    return V3Service.report_dashboard(user_id=str(user["_id"]))


@router.get("/learning")
def learning_history(
    category: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1, le=3650),
    user=Depends(AuthService.get_current_user),
):
    return V3Service.learning_history(
        user_id=str(user["_id"]), category=category, days=days
    )


@router.post("/learning", status_code=201)
def create_learning_log(
    payload: LearningLogPayload, user=Depends(AuthService.get_current_user)
):
    return V3Service.create_learning_log(
        payload.model_dump(), user_id=str(user["_id"])
    )


@router.get("/learning/latest")
def learning_latest(user=Depends(AuthService.get_current_user)):
    return V3Service.learning_latest(user_id=str(user["_id"]))


@router.get("/learning/{log_id}")
def learning_detail(log_id: str, user=Depends(AuthService.get_current_user)):
    log = V3Service.get_learning_log(log_id, user_id=str(user["_id"]))
    if not log:
        raise HTTPException(status_code=404, detail="Learning log not found")
    return log


@router.put("/learning/{log_id}")
def update_learning_log(
    log_id: str,
    payload: LearningLogPayload,
    user=Depends(AuthService.get_current_user),
):
    log = V3Service.update_learning_log(
        log_id, payload.model_dump(), user_id=str(user["_id"])
    )
    if not log:
        raise HTTPException(status_code=404, detail="Learning log not found")
    return log


@router.delete("/learning/{log_id}")
def delete_learning_log(log_id: str, user=Depends(AuthService.get_current_user)):
    deleted = V3Service.delete_learning_log(log_id, user_id=str(user["_id"]))
    if not deleted["success"]:
        raise HTTPException(status_code=404, detail="Learning log not found")
    return deleted


@router.get("/scheduler/jobs")
def scheduler_jobs(user=Depends(AuthService.get_current_user)):
    """Get user-specific scheduler jobs"""
    user_id = str(user["_id"])
    return V3Service.scheduler_jobs(user_id=user_id)


@router.get("/scheduler/status")
def scheduler_status(user=Depends(AuthService.get_current_user)):
    """Get scheduler status for current user"""
    user_id = str(user["_id"])
    return SchedulerService.status(user_id=user_id)


@router.get("/scheduler/dashboard")
def scheduler_dashboard(user=Depends(AuthService.get_current_user)):
    """Get scheduler dashboard for current user"""
    user_id = str(user["_id"])
    return SchedulerService.dashboard(user_id=user_id)


@router.post("/scheduler/start")
def scheduler_start(user=Depends(AuthService.get_current_user)):
    """Start scheduler for current user"""
    user_id = str(user["_id"])
    return {"success": True, "message": "Scheduler start requested.", "user_id": user_id}


@router.post("/scheduler/stop")
def scheduler_stop(user=Depends(AuthService.get_current_user)):
    """Stop scheduler for current user"""
    user_id = str(user["_id"])
    return {"success": True, "message": "Scheduler stop requested.", "user_id": user_id}


@router.post("/scheduler/run-market")
def run_market(user=Depends(AuthService.get_current_user)):
    """Manually run market scanner for current user"""
    user_id = str(user["_id"])
    return SchedulerService.run_market_now(user_id=user_id)


@router.post("/scheduler/run-nightly")
def run_nightly(user=Depends(AuthService.get_current_user)):
    """Manually run nightly optimization for current user"""
    user_id = str(user["_id"])
    return SchedulerService.run_nightly_now(user_id=user_id)


@router.get("/settings")
def settings_get(user=Depends(AuthService.get_current_user)):
    return V3Service.settings_get(user_id=str(user["_id"]))


@router.put("/settings")
def settings_put(payload: SettingsPayload, user=Depends(AuthService.get_current_user)):
    return V3Service.settings_put(payload.model_dump(exclude_none=True), user_id=str(user["_id"]))


@router.get("/account")
def account_get(user=Depends(AuthService.get_current_user)):
    return V3Service.account_get(user_id=str(user["_id"]))


@router.put("/account")
def account_put(payload: AccountPayload, user=Depends(AuthService.get_current_user)):
    return V3Service.account_put(payload.model_dump(exclude_none=True), user_id=str(user["_id"]))


@router.get("/symbols")
def symbols():
    return V3Service.symbols()


@router.get("/timeframes")
def timeframes():
    return V3Service.timeframes()
