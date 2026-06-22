from apscheduler.schedulers.background import BackgroundScheduler
from services.strategy_manager import run_strategy

scheduler = BackgroundScheduler()

def scan_market():

    symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT"
    ]

    for symbol in symbols:
        print(run_strategy(symbol))

def start_scheduler():

    scheduler.add_job(
        scan_market,
        "interval",
        minutes=15
    )

    scheduler.start()