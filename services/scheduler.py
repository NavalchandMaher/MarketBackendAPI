from apscheduler.schedulers.background import BackgroundScheduler

from learning_engine import LearningEngine

scheduler = BackgroundScheduler()

scheduler.add_job(
    LearningEngine.optimize,
    "cron",
    hour=0,
    minute=5
)

scheduler.start()