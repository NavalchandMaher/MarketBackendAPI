from apscheduler.schedulers.background import BackgroundScheduler
from services.learning_engine import optimize_strategy

scheduler = BackgroundScheduler()

scheduler.add_job(
    optimize_strategy,
    "cron",
    hour=0
)

scheduler.start()