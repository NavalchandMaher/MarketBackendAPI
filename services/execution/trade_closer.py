"""
Trade Closer Service
Market AI V2
"""

import time
import threading
from datetime import datetime

from db.mongodb import paper_trades, closed_trades

from services.execution.paper_trading import PaperTrading
from services.market.market_data import get_current_price

# These will be implemented later
# from services.learning_engine import LearningEngine
# from services.performance_service import PerformanceService


class TradeCloser:

    running = False

    interval = 60  # seconds

    worker = None

    # =====================================================
    # CURRENT PRICE
    # =====================================================

    @staticmethod
    def current_price(symbol):

        try:

            price = get_current_price(symbol)

            return float(price["price"])

        except Exception:

            return None

    # =====================================================
    # LOAD OPEN TRADES
    # =====================================================

    @staticmethod
    def open_trades():

        return list(paper_trades.find({"status": "OPEN"}))

    # =====================================================
    # SINGLE TRADE
    # =====================================================

    @staticmethod
    def get_trade(trade_id):

        return paper_trades.find_one({"trade_id": trade_id})

    # =====================================================
    # UPDATE TRADE
    # =====================================================

    @staticmethod
    def update_trade(trade_id, data):

        data["updated_at"] = datetime.utcnow()

        paper_trades.update_one({"trade_id": trade_id}, {"$set": data})

    # =====================================================
    # LOG
    # =====================================================

    @staticmethod
    def log(message):

        print(f"[TRADE CLOSER] {message}")

    # =====================================================
    # START SCHEDULER
    # =====================================================

    @staticmethod
    def start():

        if TradeCloser.running:

            return

        TradeCloser.running = True

        TradeCloser.worker = threading.Thread(target=TradeCloser.scheduler, daemon=True)

        TradeCloser.worker.start()

        TradeCloser.log("Scheduler Started")

    # =====================================================
    # STOP SCHEDULER
    # =====================================================

    @staticmethod
    def stop():

        TradeCloser.running = False

        TradeCloser.log("Scheduler Stopped")
        # =====================================================

    # TAKE PROFIT CHECK
    # =====================================================

    @staticmethod
    def tp_hit(trade, current_price):

        if trade["signal"] == "BUY":

            return current_price >= trade["take_profit"]

        return current_price <= trade["take_profit"]

    # =====================================================
    # STOP LOSS CHECK
    # =====================================================

    @staticmethod
    def sl_hit(trade, current_price):

        if trade["signal"] == "BUY":

            return current_price <= trade["stop_loss"]

        return current_price >= trade["stop_loss"]

    # =====================================================
    # TRAILING STOP
    # =====================================================

    @staticmethod
    def update_trailing_stop(trade, current_price, trail_percent=0.50):

        stop_loss = trade["stop_loss"]

        if trade["signal"] == "BUY":

            new_sl = current_price * (1 - trail_percent / 100)

            if new_sl > stop_loss:

                TradeCloser.update_trade(
                    trade["trade_id"], {"stop_loss": round(new_sl, 2)}
                )

                TradeCloser.log(
                    f"{trade['trade_id']} " f"Trailing SL -> " f"{round(new_sl,2)}"
                )

        else:

            new_sl = current_price * (1 + trail_percent / 100)

            if new_sl < stop_loss:

                TradeCloser.update_trade(
                    trade["trade_id"], {"stop_loss": round(new_sl, 2)}
                )

                TradeCloser.log(
                    f"{trade['trade_id']} " f"Trailing SL -> " f"{round(new_sl,2)}"
                )

    # =====================================================
    # TRADE DECISION
    # =====================================================

    @staticmethod
    def evaluate_trade(trade):

        current_price = TradeCloser.current_price(trade["symbol"])

        if current_price is None:

            return

        # ---------- TP ----------

        if TradeCloser.tp_hit(trade, current_price):

            TradeCloser.log(f"{trade['trade_id']} " f"TARGET HIT")

            PaperTrading.close_trade(trade["trade_id"], current_price, "TARGET")

            return

        # ---------- SL ----------

        if TradeCloser.sl_hit(trade, current_price):

            TradeCloser.log(f"{trade['trade_id']} " f"STOP LOSS HIT")

            PaperTrading.close_trade(trade["trade_id"], current_price, "STOP LOSS")

            return

        # ---------- TRAILING ----------

        TradeCloser.update_trailing_stop(trade, current_price)
        # =====================================================

    # PROCESS ALL OPEN TRADES
    # =====================================================

    @staticmethod
    def process_open_trades():

        trades = TradeCloser.open_trades()

        if len(trades) == 0:

            TradeCloser.log("No open trades.")

            return

        TradeCloser.log(f"Checking {len(trades)} open trade(s)...")

        for trade in trades:

            try:

                TradeCloser.evaluate_trade(trade)

            except Exception as ex:

                TradeCloser.log(f"{trade.get('trade_id')} Error : {ex}")

    # =====================================================
    # UPDATE PERFORMANCE
    # =====================================================

    @staticmethod
    def update_performance():

        try:

            # Will be implemented in performance_service.py
            # PerformanceService.calculate()

            TradeCloser.log("Performance Updated")

        except Exception as ex:

            TradeCloser.log(f"Performance Error : {ex}")

    # =====================================================
    # LEARNING ENGINE
    # =====================================================

    @staticmethod
    def learning_update():

        try:

            # Will be implemented later

            # LearningEngine.learn()

            TradeCloser.log("Learning Model Updated")

        except Exception as ex:

            TradeCloser.log(f"Learning Error : {ex}")

    # =====================================================
    # AFTER TRADE CLOSED
    # =====================================================

    @staticmethod
    def after_close():

        TradeCloser.update_performance()

        TradeCloser.learning_update()

    # =====================================================
    # CHECK CLOSED TRADES
    # =====================================================

    @staticmethod
    def check_recently_closed():

        cursor = closed_trades.find().sort("closed_at", -1).limit(10)

        for trade in cursor:

            TradeCloser.log(
                f"CLOSED "
                f"{trade['trade_id']} "
                f"{trade['result']} "
                f"PnL={trade['pnl']}"
            )

    # =====================================================
    # PROCESS CYCLE
    # =====================================================

    @staticmethod
    def process():

        try:

            TradeCloser.process_open_trades()

            TradeCloser.after_close()

            TradeCloser.check_recently_closed()

        except Exception as ex:

            TradeCloser.log(f"Process Error : {ex}")
        # =====================================================

    # SCHEDULER
    # =====================================================

    @staticmethod
    def scheduler():

        TradeCloser.log("Trade Scheduler Running...")

        while TradeCloser.running:

            try:

                TradeCloser.process()

            except Exception as ex:

                TradeCloser.log(f"Scheduler Error : {ex}")

            time.sleep(TradeCloser.interval)

    # =====================================================
    # MANUAL CLOSE
    # =====================================================

    @staticmethod
    def manual_close(trade_id, reason="MANUAL"):

        trade = TradeCloser.get_trade(trade_id)

        if trade is None:

            return {"success": False, "message": "Trade not found."}

        current_price = TradeCloser.current_price(trade["symbol"])

        if current_price is None:

            return {"success": False, "message": "Unable to fetch current price."}

        PaperTrading.close_trade(trade_id, current_price, reason)

        TradeCloser.after_close()

        TradeCloser.log(f"Trade {trade_id} manually closed.")

        return {
            "success": True,
            "trade_id": trade_id,
            "exit_price": current_price,
            "reason": reason,
        }

    # =====================================================
    # STATUS
    # =====================================================

    @staticmethod
    def status():

        return {
            "running": TradeCloser.running,
            "interval_seconds": TradeCloser.interval,
            "open_trades": len(TradeCloser.open_trades()),
            "balance": PaperTrading.balance,
        }

    # =====================================================
    # DASHBOARD
    # =====================================================

    @staticmethod
    def dashboard():

        return {
            "scheduler": TradeCloser.status(),
            "account": PaperTrading.account_summary(),
            "open_trades": PaperTrading.get_open_trades(),
            "closed_trades": PaperTrading.get_closed_trades(20),
        }

    # =====================================================
    # FORCE RUN
    # =====================================================

    @staticmethod
    def run_once():

        TradeCloser.process()

        return {"success": True, "message": "Trade check completed."}

    # =====================================================
    # CHANGE INTERVAL
    # =====================================================

    @staticmethod
    def set_interval(seconds):

        if seconds < 10:

            seconds = 10

        TradeCloser.interval = seconds

        TradeCloser.log(f"Scheduler interval set to " f"{seconds} seconds")

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    @staticmethod
    def health():

        return {
            "service": "TradeCloser",
            "status": "RUNNING" if TradeCloser.running else "STOPPED",
            "worker": TradeCloser.worker is not None,
            "interval": TradeCloser.interval,
            "timestamp": datetime.utcnow(),
        }


# =====================================================
# AUTO START
# =====================================================

TradeCloser.start()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    TradeCloser.start()

    while True:

        time.sleep(60)
