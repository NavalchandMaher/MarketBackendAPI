from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from services.signal_engine import analyze_market
from services.paper_trading import PaperTrading
from services.trade_closer import TradeCloser

from services.backtester import BackTester
from services.learning_engine import LearningEngine
from services.strategy_optimizer import StrategyOptimizer
from services.performance_service import PerformanceService


class SchedulerService:

    scheduler = BackgroundScheduler()

    # ==========================================
    # EVERY MINUTE
    # ==========================================

    @staticmethod
    def market_cycle():

        print(f"[{datetime.utcnow()}] Running Market Cycle")

        try:

            # 1. Analyze Market

            result = analyze_market(
                symbol="BTCUSDT",
                timeframe="5m"
            )

            if result["signal"] in ["BUY", "SELL"]:

                PaperTrading.open_trade(result)

            # 2. Check Open Trades

            TradeCloser.process()

        except Exception as ex:

            print(ex)

    # ==========================================
    # HEALTH
    # ==========================================

    @staticmethod
    def health():

        return {"status": "RUNNING", "jobs": len(SchedulerService.scheduler.get_jobs())}

    # =====================================================
    # NIGHTLY AI CYCLE
    # =====================================================

    @staticmethod
    def nightly_cycle():

        print(f"[{datetime.utcnow()}] Starting Nightly AI Cycle")

        try:

            # ----------------------------------------
            # 1. Run Backtest
            # ----------------------------------------

            backtest = BackTester.run(symbol="BTCUSDT", timeframe="5m", days=365)

            print("✓ Backtest Completed")

            # ----------------------------------------
            # 2. Learning Engine
            # ----------------------------------------

            learning = LearningEngine.learn()

            print("✓ Learning Completed")

            # ----------------------------------------
            # 3. Strategy Optimizer
            # ----------------------------------------

            optimizer = StrategyOptimizer.run()

            print("✓ Strategy Optimization Completed")

            # ----------------------------------------
            # 4. Performance Dashboard
            # ----------------------------------------

            dashboard = PerformanceService.dashboard()

            print("✓ Performance Updated")

            return {
                "success": True,
                "backtest": backtest,
                "learning": learning,
                "optimizer": optimizer,
                "dashboard": dashboard,
                "completed_at": datetime.utcnow(),
            }

        except Exception as ex:

            print(f"Nightly Cycle Error : {ex}")

            return {
                "success": False,
                "error": str(ex),
                "completed_at": datetime.utcnow(),
            }

    # =====================================================
    # MANUAL BACKTEST
    # =====================================================

    @staticmethod
    def run_backtest():

        return BackTester.run(symbol="BTCUSDT", timeframe="5m", days=365)

    # =====================================================
    # MANUAL LEARNING
    # =====================================================

    @staticmethod
    def run_learning():

        return LearningEngine.learn()

    # =====================================================
    # MANUAL OPTIMIZER
    # =====================================================

    @staticmethod
    def run_optimizer():

        return StrategyOptimizer.run()

    # =====================================================
    # PERFORMANCE REFRESH
    # =====================================================

    @staticmethod
    def refresh_dashboard():

        return PerformanceService.dashboard()

        # =====================================================

    # START SCHEDULER
    # =====================================================

    @staticmethod
    def start():

        if SchedulerService.scheduler.running:

            print("Scheduler already running.")
            return

        # ----------------------------------------
        # Every Minute Market Cycle
        # ----------------------------------------

        SchedulerService.scheduler.add_job(
            SchedulerService.market_cycle,
            trigger="interval",
            minutes=1,
            id="market_cycle",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        # ----------------------------------------
        # Nightly AI Cycle
        # Every day at 12:30 AM
        # ----------------------------------------

        SchedulerService.scheduler.add_job(
            SchedulerService.nightly_cycle,
            trigger="cron",
            hour=0,
            minute=30,
            id="nightly_cycle",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        SchedulerService.scheduler.start()

        print("========================================")
        print(" AI Scheduler Started")
        print("========================================")
        print(" Market Cycle : Every 1 Minute")
        print(" Nightly AI   : 00:30 Daily")
        print("========================================")

    # =====================================================
    # STOP SCHEDULER
    # =====================================================

    @staticmethod
    def stop():

        if SchedulerService.scheduler.running:

            SchedulerService.scheduler.shutdown(wait=False)

            print("Scheduler stopped.")

    # =====================================================
    # RESTART SCHEDULER
    # =====================================================

    @staticmethod
    def restart():

        SchedulerService.stop()

        SchedulerService.scheduler = BackgroundScheduler()

        SchedulerService.start()

    # =====================================================
    # REGISTER JOBS
    # =====================================================

    @staticmethod
    def register_jobs():

        jobs = SchedulerService.scheduler.get_jobs()

        print("========================================")
        print("Registered Jobs")
        print("========================================")

        if not jobs:

            print("No Jobs Registered")

        for job in jobs:

            print(f"{job.id} | " f"Next Run : {job.next_run_time}")

    # =====================================================
    # SCHEDULER STATUS
    # =====================================================

    @staticmethod
    def status():

        jobs = []

        for job in SchedulerService.scheduler.get_jobs():

            jobs.append(
                {
                    "id": job.id,
                    "next_run": str(job.next_run_time),
                    "trigger": str(job.trigger),
                }
            )

        return {
            "running": SchedulerService.scheduler.running,
            "total_jobs": len(jobs),
            "jobs": jobs,
        }

    # =====================================================
    # FORCE MARKET CYCLE
    # =====================================================

    @staticmethod
    def run_market_now():

        SchedulerService.market_cycle()

        return {"success": True, "message": "Market cycle executed."}

    # =====================================================
    # FORCE NIGHTLY CYCLE
    # =====================================================

    @staticmethod
    def run_nightly_now():

        return SchedulerService.nightly_cycle()

        # =====================================================

    # DASHBOARD
    # =====================================================

    @staticmethod
    def dashboard():

        return {
            "scheduler": SchedulerService.status(),
            "market_health": {"market_cycle": "RUNNING"},
            "jobs": [
                {"name": "Market Cycle", "frequency": "Every 1 Minute"},
                {"name": "Nightly AI", "frequency": "00:30 Daily"},
            ],
            "timestamp": datetime.utcnow(),
        }

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    @staticmethod
    def health():

        return {
            "service": "SchedulerService",
            "status": "RUNNING" if SchedulerService.scheduler.running else "STOPPED",
            "jobs": len(SchedulerService.scheduler.get_jobs()),
            "timestamp": datetime.utcnow(),
        }

    # =====================================================
    # FASTAPI STARTUP
    # =====================================================

    @staticmethod
    def startup():

        print()

        print("============================================")
        print("      MARKET AI V2 STARTING")
        print("============================================")

        SchedulerService.start()

        SchedulerService.register_jobs()

        print("============================================")
        print("Application Started Successfully")
        print("============================================")

    # =====================================================
    # FASTAPI SHUTDOWN
    # =====================================================

    @staticmethod
    def shutdown():

        print()

        print("============================================")
        print("Stopping Scheduler...")
        print("============================================")

        SchedulerService.stop()

        print("Application Shutdown Complete")


# =====================================================
# AUTO START (optional)
# =====================================================

AUTO_START = False

if AUTO_START:

    SchedulerService.start()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    SchedulerService.start()

    try:

        import time

        while True:

            time.sleep(60)

    except KeyboardInterrupt:

        SchedulerService.stop()
