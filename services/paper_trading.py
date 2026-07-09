"""
Paper Trading Engine
Market AI V2
"""

import uuid

from datetime import datetime

from config import INITIAL_BALANCE, RISK_PERCENT, MAX_OPEN_TRADES

from db.mongodb import paper_trades, closed_trades


class PaperTrading:

    balance = INITIAL_BALANCE

    # ======================================================
    # POSITION SIZE
    # ======================================================

    @staticmethod
    def calculate_position_size(entry_price, stop_loss):

        risk_amount = PaperTrading.balance * RISK_PERCENT / 100

        stop_distance = abs(entry_price - stop_loss)

        if stop_distance == 0:

            return 0

        quantity = risk_amount / stop_distance

        return round(quantity, 4)

    # ======================================================
    # TP / SL
    # ======================================================

    @staticmethod
    def calculate_tp_sl(signal, entry_price, tp_percent, sl_percent):

        if signal == "BUY":

            take_profit = entry_price * (1 + tp_percent / 100)

            stop_loss = entry_price * (1 - sl_percent / 100)

        else:

            take_profit = entry_price * (1 - tp_percent / 100)

            stop_loss = entry_price * (1 + sl_percent / 100)

        return (round(take_profit, 2), round(stop_loss, 2))

    # ======================================================
    # DUPLICATE CHECK
    # ======================================================

    @staticmethod
    def trade_exists(symbol, timeframe, user_id=None):
        query = {"symbol": symbol, "timeframe": timeframe, "status": "OPEN"}
        if user_id:
            query["user_id"] = user_id
        return paper_trades.find_one(query) is not None

    # ======================================================
    # OPEN TRADE LIMIT
    # ======================================================

    @staticmethod
    def max_trade_limit_reached(user_id=None):
        query = {"status": "OPEN"}
        if user_id:
            query["user_id"] = user_id
        count = paper_trades.count_documents(query)

        return count >= MAX_OPEN_TRADES

    # ======================================================
    # TRADE ID
    # ======================================================

    @staticmethod
    def generate_trade_id():

        return "TRD-" + uuid.uuid4().hex[:10].upper()

    # ======================================================
    # CREATE TRADE DOCUMENT
    # ======================================================

    @staticmethod
    def create_trade_document(
        symbol,
        timeframe,
        signal,
        strategy_name,
        strategy_version,
        entry_price,
        confidence,
        market_regime,
        indicators,
        tp_percent,
        sl_percent,
    ):

        tp, sl = PaperTrading.calculate_tp_sl(
            signal, entry_price, tp_percent, sl_percent
        )

        quantity = PaperTrading.calculate_position_size(entry_price, sl)

        return {
            "trade_id": PaperTrading.generate_trade_id(),
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "strategy_name": strategy_name,
            "strategy_version": strategy_version,
            "entry_price": round(entry_price, 2),
            "take_profit": tp,
            "stop_loss": sl,
            "quantity": quantity,
            "confidence": confidence,
            "market_regime": market_regime,
            "indicators": indicators,
            "status": "OPEN",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # ======================================================

    # OPEN TRADE
    # ======================================================

    @staticmethod
    def open_trade(trade_data):

        try:

            signal = trade_data.get("signal")

            if signal == "WAIT":

                return {"success": False, "message": "WAIT signal. Trade not opened."}

            symbol = trade_data["symbol"]

            timeframe = trade_data["timeframe"]

            user_id = trade_data.get("user_id")

            if PaperTrading.trade_exists(symbol, timeframe, user_id=user_id):

                return {"success": False, "message": "Open trade already exists."}

            if PaperTrading.max_trade_limit_reached(user_id=user_id):

                return {"success": False, "message": "Maximum open trades reached."}

            strategy_name = trade_data.get("strategy_name", "DEFAULT")

            strategy_version = trade_data.get("strategy_version", 1)

            confidence = trade_data.get("confidence", 0)

            market_regime = trade_data.get("market_regime", "UNKNOWN")

            indicators = trade_data.get("indicators", {})

            tp_percent = trade_data.get("tp_percent", 2.0)

            sl_percent = trade_data.get("sl_percent", 1.0)

            trade = PaperTrading.create_trade_document(
                symbol=symbol,
                timeframe=timeframe,
                signal=signal,
                strategy_name=strategy_name,
                strategy_version=strategy_version,
                entry_price=trade_data["price"],
                confidence=confidence,
                market_regime=market_regime,
                indicators=indicators,
                tp_percent=tp_percent,
                sl_percent=sl_percent,
            )

            if user_id:
                trade["user_id"] = user_id

            result = paper_trades.insert_one(trade)

            trade["_id"] = str(result.inserted_id)

            print(
                f"[PAPER TRADE OPENED] "
                f"{trade['trade_id']} "
                f"{trade['signal']} "
                f"{trade['symbol']} "
                f"@ {trade['entry_price']}"
            )

            return {"success": True, "message": "Paper trade opened.", "trade": trade}

        except Exception as ex:

            print("Paper Trading Error:", ex)

            return {"success": False, "message": str(ex)}

        # ======================================================

    # GET OPEN TRADES
    # ======================================================

    @staticmethod
    def get_open_trades(user_id=None):

        trades = []

        query = {"status": "OPEN"}
        if user_id:
            query["user_id"] = user_id

        cursor = paper_trades.find(query).sort("created_at", -1)

        for trade in cursor:

            trade["_id"] = str(trade["_id"])

            trades.append(trade)

        return trades

    # ======================================================
    # GET CLOSED TRADES
    # ======================================================

    @staticmethod
    def get_closed_trades(limit=100, user_id=None):

        trades = []

        query = {}
        if user_id:
            query["user_id"] = user_id

        cursor = closed_trades.find(query).sort("closed_at", -1).limit(limit)

        for trade in cursor:

            trade["_id"] = str(trade["_id"])

            trades.append(trade)

        return trades

    # ======================================================
    # GET ALL TRADES
    # ======================================================

    @staticmethod
    def get_all_trades(limit=500, user_id=None):

        trades = []

        query = {}
        if user_id:
            query["user_id"] = user_id

        cursor = paper_trades.find(query).sort("created_at", -1).limit(limit)

        for trade in cursor:

            trade["_id"] = str(trade["_id"])

            trades.append(trade)

        return trades

    # ======================================================
    # GET TRADE BY ID
    # ======================================================

    @staticmethod
    def get_trade(trade_id, user_id=None):

        query = {"trade_id": trade_id}
        if user_id:
            query["user_id"] = user_id

        trade = paper_trades.find_one(query)

        if trade:

            trade["_id"] = str(trade["_id"])

        return trade

    # ======================================================
    # GET TRADE HISTORY
    # ======================================================

    @staticmethod
    def trade_history(symbol=None, strategy=None, status=None, user_id=None):

        query = {}

        if symbol:

            query["symbol"] = symbol

        if strategy:

            query["strategy_name"] = strategy

        if status:

            query["status"] = status

        history = []

        cursor = paper_trades.find(query).sort("created_at", -1)

        for trade in cursor:

            trade["_id"] = str(trade["_id"])

            history.append(trade)

        return history

    # ======================================================
    # UPDATE TRADE
    # ======================================================

    @staticmethod
    def update_trade(trade_id, update_data, user_id=None):

        update_data["updated_at"] = datetime.utcnow()

        query = {"trade_id": trade_id}
        if user_id:
            query["user_id"] = user_id

        result = paper_trades.update_one(query, {"$set": update_data})

        return result.modified_count > 0

    # ======================================================
    # DELETE TRADE
    # ======================================================

    @staticmethod
    def delete_trade(trade_id, user_id=None):

        query = {"trade_id": trade_id}
        if user_id:
            query["user_id"] = user_id

        result = paper_trades.delete_one(query)

        return result.deleted_count > 0

    # ======================================================
    # COUNT OPEN TRADES
    # ======================================================

    @staticmethod
    def open_trade_count(user_id=None):
        query = {"status": "OPEN"}
        if user_id:
            query["user_id"] = user_id
        return paper_trades.count_documents(query)

    # ======================================================
    # OPEN TRADES BY SYMBOL
    # ======================================================

    @staticmethod
    def get_symbol_trades(symbol, user_id=None):

        trades = []

        query = {"symbol": symbol, "status": "OPEN"}
        if user_id:
            query["user_id"] = user_id

        cursor = paper_trades.find(query)

        for trade in cursor:

            trade["_id"] = str(trade["_id"])

            trades.append(trade)

        return trades

        # ======================================================

    # CLOSE TRADE
    # ======================================================

    @staticmethod
    def close_trade(trade_id, exit_price, reason="TARGET", user_id=None):

        query = {"trade_id": trade_id}
        if user_id:
            query["user_id"] = user_id

        trade = paper_trades.find_one(query)

        if not trade:

            return False

        if trade["status"] != "OPEN":

            return False

        if trade["signal"] == "BUY":

            pnl = (exit_price - trade["entry_price"]) * trade["quantity"]

        else:

            pnl = (trade["entry_price"] - exit_price) * trade["quantity"]

        pnl = round(pnl, 2)

        pnl_percent = round((pnl / (trade["entry_price"] * trade["quantity"])) * 100, 2)

        result = "WIN" if pnl > 0 else "LOSS"

        PaperTrading.balance += pnl

        trade["exit_price"] = round(exit_price, 2)

        trade["closed_at"] = datetime.utcnow()

        trade["updated_at"] = datetime.utcnow()

        trade["status"] = "CLOSED"

        trade["result"] = result

        trade["pnl"] = pnl

        trade["pnl_percent"] = pnl_percent

        trade["close_reason"] = reason

        paper_trades.delete_one({"_id": trade["_id"]})

        closed_trades.insert_one(trade)

        return True

    # ======================================================
    # ACCOUNT SUMMARY
    # ======================================================

    @staticmethod
    def account_summary(user_id=None):

        query = {"status": "OPEN"}
        if user_id:
            query["user_id"] = user_id

        open_trades = paper_trades.count_documents(query)

        closed_query = {}
        if user_id:
            closed_query["user_id"] = user_id

        closed = list(closed_trades.find(closed_query))

        wins = sum(1 for t in closed if t["result"] == "WIN")

        losses = sum(1 for t in closed if t["result"] == "LOSS")

        total_profit = round(sum(t["pnl"] for t in closed), 2)

        total = wins + losses

        win_rate = 0

        if total > 0:

            win_rate = round(wins / total * 100, 2)

        return {
            "balance": round(PaperTrading.balance, 2),
            "initial_balance": INITIAL_BALANCE,
            "profit": total_profit,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "open_trades": open_trades,
            "closed_trades": total,
        }

    # ======================================================
    # TOTAL PNL
    # ======================================================

    @staticmethod
    def total_pnl(user_id=None):

        query = {}
        if user_id:
            query["user_id"] = user_id

        trades = closed_trades.find(query)

        return round(sum(t["pnl"] for t in trades), 2)

    # ======================================================
    # RESET PAPER ACCOUNT
    # ======================================================

    @staticmethod
    def reset(user_id=None):

        query = {}
        if user_id:
            query["user_id"] = user_id

        paper_trades.delete_many(query)

        closed_trades.delete_many(query)

        PaperTrading.balance = INITIAL_BALANCE

        return True

    # ======================================================
    # DASHBOARD
    # ======================================================

    @staticmethod
    def dashboard(user_id=None):

        return {
            "account": PaperTrading.account_summary(user_id=user_id),
            "open": PaperTrading.get_open_trades(user_id=user_id),
            "history": PaperTrading.get_closed_trades(20, user_id=user_id),
        }
