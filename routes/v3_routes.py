from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from services.v3_service import V3Service
from services.auth_service import AuthService

router = APIRouter(prefix="/v3", tags=["v3"])


class StrategyPayload(BaseModel):
    strategy_name: Optional[str] = None
    version: Optional[int] = 1
    enabled: Optional[bool] = True
    paper_mode: Optional[bool] = True
    live_mode: Optional[bool] = False
    priority: Optional[int] = 1
    symbol: Optional[str] = "BTCUSDT"
    timeframe: Optional[str] = "5m"
    risk_percent: Optional[float] = 1.0
    tp: Optional[float] = 2.0
    sl: Optional[float] = 1.0
    indicator_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BacktestPayload(BaseModel):
    symbol: Optional[str] = "BTCUSDT"
    timeframe: Optional[str] = "5m"
    days: Optional[int] = 365


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


@router.get("/dashboard")
def dashboard(user=Depends(AuthService.get_current_user)):
    return V3Service.dashboard_summary(user_id=str(user["_id"]))


@router.get("/strategies")
def strategies_list(user=Depends(AuthService.get_current_user)):
    return V3Service.list_strategies(user_id=str(user["_id"]))


@router.get("/strategies/{strategy_id}")
def strategy_detail(strategy_id: str, user=Depends(AuthService.get_current_user)):
    strategy = V3Service.get_strategy(strategy_id, user_id=str(user["_id"]))
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("/strategies", status_code=201)
def create_strategy(payload: StrategyPayload, user=Depends(AuthService.get_current_user)):
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    return V3Service.create_strategy(data)


@router.put("/strategies/{strategy_id}")
def update_strategy(strategy_id: str, payload: StrategyPayload, user=Depends(AuthService.get_current_user)):
    updated = V3Service.update_strategy(strategy_id, payload.model_dump(exclude_none=True), user_id=str(user["_id"]))
    if not updated:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return updated


@router.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: str, user=Depends(AuthService.get_current_user)):
    return V3Service.delete_strategy(strategy_id, user_id=str(user["_id"]))


@router.post("/backtest/run")
def run_backtest(payload: BacktestPayload, user=Depends(AuthService.get_current_user)):
    data = payload.model_dump(exclude_none=True)
    data["user_id"] = str(user["_id"])
    return V3Service.run_backtest(data)


@router.get("/backtest/{backtest_id}")
def get_backtest(backtest_id: str, user=Depends(AuthService.get_current_user)):
    backtest = V3Service.get_backtest(backtest_id, user_id=str(user["_id"]))
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtest


@router.get("/backtest/history")
def list_backtests(user=Depends(AuthService.get_current_user)):
    return V3Service.list_backtests(user_id=str(user["_id"]))


@router.delete("/backtest/{backtest_id}")
def delete_backtest(backtest_id: str, user=Depends(AuthService.get_current_user)):
    return V3Service.delete_backtest(backtest_id, user_id=str(user["_id"]))


@router.post("/paper/start")
def paper_start(user=Depends(AuthService.get_current_user)):
    return V3Service.paper_start(user_id=str(user["_id"]))


@router.post("/paper/stop")
def paper_stop():
    return V3Service.paper_stop()


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
def broker_connect(payload: BrokerPayload):
    return V3Service.broker_connect(payload.model_dump(exclude_none=True))


@router.post("/broker/test")
def broker_test(payload: BrokerPayload):
    return V3Service.broker_test(payload.model_dump(exclude_none=True))


@router.post("/broker/disconnect")
def broker_disconnect(payload: BrokerPayload):
    return V3Service.broker_disconnect(payload.model_dump(exclude_none=True))


@router.get("/reports/dashboard")
def reports_dashboard():
    return V3Service.report_dashboard()


@router.get("/reports/daily")
def reports_daily():
    return V3Service.report_dashboard()


@router.get("/reports/monthly")
def reports_monthly():
    return V3Service.report_dashboard()


@router.get("/reports/yearly")
def reports_yearly():
    return V3Service.report_dashboard()


@router.get("/reports/equity")
def reports_equity():
    return V3Service.report_dashboard()


@router.get("/reports/performance")
def reports_performance():
    return V3Service.report_dashboard()


@router.get("/learning")
def learning_history(user=Depends(AuthService.get_current_user)):
    return V3Service.learning_history(user_id=str(user["_id"]))


@router.get("/learning/latest")
def learning_latest(user=Depends(AuthService.get_current_user)):
    return V3Service.learning_latest(user_id=str(user["_id"]))


@router.get("/scheduler/jobs")
def scheduler_jobs():
    return V3Service.scheduler_jobs()


@router.post("/scheduler/start")
def scheduler_start():
    return {"success": True, "message": "Scheduler start requested."}


@router.post("/scheduler/stop")
def scheduler_stop():
    return {"success": True, "message": "Scheduler stop requested."}


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
