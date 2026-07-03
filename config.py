"""
Market AI V2 Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv("market.env")

# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "Market AI V2"

VERSION = "2.0.0"

DEBUG = True

# ==========================================================
# MONGODB
# ==========================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

DATABASE_NAME = os.getenv("DATABASE_NAME", "MarketAI_V2")

# ==========================================================
# BINANCE
# ==========================================================

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")

BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

USE_TESTNET = os.getenv("USE_TESTNET", "false").lower() == "true"

# ==========================================================
# DEFAULT MARKET
# ==========================================================

DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")

DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "5m")

# ==========================================================
# PAPER TRADING
# ==========================================================

INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "100000"))

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "2"))

MAX_OPEN_TRADES = int(os.getenv("MAX_OPEN_TRADES", "3"))

# ==========================================================
# STRATEGY
# ==========================================================

DEFAULT_BUY_THRESHOLD = int(os.getenv("BUY_THRESHOLD", "3"))

DEFAULT_SELL_THRESHOLD = int(os.getenv("SELL_THRESHOLD", "-3"))

DEFAULT_TP_PERCENT = float(os.getenv("TP_PERCENT", "2"))

DEFAULT_SL_PERCENT = float(os.getenv("SL_PERCENT", "1"))

# ==========================================================
# BACKTEST
# ==========================================================

BACKTEST_DAYS = int(os.getenv("BACKTEST_DAYS", "365"))

BACKTEST_INITIAL_CAPITAL = float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100000"))

# ==========================================================
# LEARNING ENGINE
# ==========================================================

AUTO_LEARNING = os.getenv("AUTO_LEARNING", "true").lower() == "true"

LEARNING_RATE = float(os.getenv("LEARNING_RATE", "0.10"))

MIN_WIN_RATE = float(os.getenv("MIN_WIN_RATE", "60"))

# ==========================================================
# SCHEDULER
# ==========================================================

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

TRADE_CHECK_INTERVAL = int(os.getenv("TRADE_CHECK_INTERVAL", "60"))

BACKTEST_INTERVAL = int(os.getenv("BACKTEST_INTERVAL", "86400"))

# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==========================================================
# CORS
# ==========================================================

ALLOWED_ORIGINS = ["*"]
