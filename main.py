from fastapi import FastAPI

from services.strategy_manager import run_strategy
from scheduler.jobs import start_scheduler

app = FastAPI()

start_scheduler()

@app.get("/")
def home():
    return {
        "app": "Paper Trading Engine",
        "status": "running"
    }

@app.get("/signal/{symbol}")
def signal(symbol: str):

    return run_strategy(symbol)