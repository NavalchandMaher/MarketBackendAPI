"""
Market Data Service
Market AI V2
"""

import time
import ccxt
import pandas as pd

from functools import wraps

from config import BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_TESTNET


class MarketDataService:

    _instance = None

    _exchange = None

    _cache = {}

    CACHE_SECONDS = 5

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance._initialize()

        return cls._instance

    def _initialize(self):

        exchange = ccxt.binance(
            {
                "apiKey": BINANCE_API_KEY,
                "secret": BINANCE_SECRET_KEY,
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
            }
        )

        if USE_TESTNET:

            exchange.set_sandbox_mode(True)

        self._exchange = exchange

    @property
    def exchange(self):

        return self._exchange


market = MarketDataService()


# ===========================================================
# RETRY DECORATOR
# ===========================================================


def retry(max_retry=3):

    def wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):

            last_error = None

            for _ in range(max_retry):

                try:

                    return func(*args, **kwargs)

                except Exception as ex:

                    last_error = ex

                    time.sleep(1)

            raise last_error

        return inner

    return wrapper


# ===========================================================
# CACHE DECORATOR
# ===========================================================


def cache(seconds=5):

    def wrapper(func):

        @wraps(func)
        def inner(*args, **kwargs):

            key = str(func.__name__) + str(args) + str(kwargs)

            current = time.time()

            if key in market._cache:

                value, timestamp = market._cache[key]

                if current - timestamp < seconds:

                    return value

            value = func(*args, **kwargs)

            market._cache[key] = (value, current)

            return value

        return inner

    return wrapper


# ===========================================================
# SYMBOL
# ===========================================================


def to_pair(symbol):

    if "/" in symbol:

        return symbol

    return symbol.replace("USDT", "/USDT")


# ===========================================================
# HISTORICAL DATA
# ===========================================================


@retry()
@cache(seconds=3)
def get_ohlcv(symbol, timeframe="5m", limit=300):

    pair = to_pair(symbol)

    candles = market.exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(
        candles, columns=["time", "open", "high", "low", "close", "volume"]
    )

    df["time"] = pd.to_datetime(df["time"], unit="ms")

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


# ===========================================================
# MULTI TIMEFRAME
# ===========================================================


@retry()
def get_multi_timeframe_data(symbol):

    data = {}

    timeframes = ["1m", "5m", "15m", "1h", "4h"]

    for tf in timeframes:

        data[tf] = get_ohlcv(symbol=symbol, timeframe=tf, limit=300)

    return data


# ===========================================================
# CURRENT PRICE
# ===========================================================


@retry()
@cache(seconds=2)
def get_current_price(symbol):

    pair = to_pair(symbol)

    ticker = market.exchange.fetch_ticker(pair)

    return {
        "symbol": symbol,
        "price": float(ticker["last"]),
        "bid": float(ticker["bid"]),
        "ask": float(ticker["ask"]),
        "high": float(ticker["high"]),
        "low": float(ticker["low"]),
        "volume": float(ticker["baseVolume"]),
        "change_percent": float(ticker["percentage"]),
    }


# ===========================================================
# LATEST CANDLE
# ===========================================================


def get_latest_candle(symbol, timeframe="5m"):

    df = get_ohlcv(symbol, timeframe, limit=2)

    return df.iloc[-1]


# ===========================================================
# PREVIOUS CANDLE
# ===========================================================


def get_previous_candle(symbol, timeframe="5m"):

    df = get_ohlcv(symbol, timeframe, limit=3)

    return df.iloc[-2]


# ===========================================================
# OPEN INTEREST
# ===========================================================

LAST_OPEN_INTEREST = {}


@retry()
@cache(seconds=5)
def get_open_interest(symbol):

    pair = to_pair(symbol)

    try:

        data = market.exchange.fetch_open_interest(pair)

        current = float(data.get("openInterest", 0))

        previous = LAST_OPEN_INTEREST.get(pair, current)

        LAST_OPEN_INTEREST[pair] = current

        change = 0

        if previous > 0:

            change = round(((current - previous) / previous) * 100, 2)

        return {"current": current, "previous": previous, "change_pct": change}

    except Exception:

        return {"current": 0, "previous": 0, "change_pct": 0}


# ===========================================================
# FUNDING RATE
# ===========================================================


@retry()
@cache(seconds=30)
def get_funding_rate(symbol):

    pair = to_pair(symbol)

    try:

        data = market.exchange.fetch_funding_rate(pair)

        return {
            "funding_rate": float(data.get("fundingRate", 0)),
            "next_funding": data.get("fundingDatetime"),
        }

    except Exception:

        return {"funding_rate": 0, "next_funding": None}


# ===========================================================
# ORDER BOOK
# ===========================================================


@retry()
@cache(seconds=2)
def get_order_book(symbol, limit=20):

    pair = to_pair(symbol)

    try:

        book = market.exchange.fetch_order_book(pair, limit)

        bids = book["bids"]

        asks = book["asks"]

        total_bid = sum(x[1] for x in bids)

        total_ask = sum(x[1] for x in asks)

        ratio = 1

        if total_ask > 0:

            ratio = round(total_bid / total_ask, 2)

        return {
            "bids": bids,
            "asks": asks,
            "bid_volume": round(total_bid, 2),
            "ask_volume": round(total_ask, 2),
            "bid_ask_ratio": ratio,
        }

    except Exception:

        return {
            "bids": [],
            "asks": [],
            "bid_volume": 0,
            "ask_volume": 0,
            "bid_ask_ratio": 1,
        }


# ===========================================================
# MARKET SNAPSHOT
# ===========================================================


def get_market_snapshot(symbol, timeframe="5m"):

    price = get_current_price(symbol)

    oi = get_open_interest(symbol)

    funding = get_funding_rate(symbol)

    orderbook = get_order_book(symbol)

    latest = get_latest_candle(symbol, timeframe)

    previous = get_previous_candle(symbol, timeframe)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "price": price,
        "open_interest": oi,
        "funding": funding,
        "orderbook": orderbook,
        "latest_close": float(latest["close"]),
        "previous_close": float(previous["close"]),
        "latest_volume": float(latest["volume"]),
        "previous_volume": float(previous["volume"]),
    }


# ===========================================================
# EXCHANGE INFO
# ===========================================================


@retry()
@cache(seconds=300)
def get_exchange_info():

    try:

        markets = market.exchange.load_markets()

        return {
            "exchange": market.exchange.id,
            "total_markets": len(markets),
            "markets": list(markets.keys()),
        }

    except Exception:

        return {"exchange": "BINANCE", "total_markets": 0, "markets": []}


# ===========================================================
# AVAILABLE SYMBOLS
# ===========================================================


@retry()
@cache(seconds=300)
def get_symbols():

    try:

        markets = market.exchange.load_markets()

        symbols = []

        for symbol in markets.keys():

            if "/USDT" in symbol:

                symbols.append(symbol.replace("/", ""))

        symbols.sort()

        return symbols

    except Exception:

        return []


# ===========================================================
# AVAILABLE TIMEFRAMES
# ===========================================================


def get_supported_timeframes():

    return ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]


# ===========================================================
# SERVER TIME
# ===========================================================


@retry()
def get_server_time():

    try:

        timestamp = market.exchange.fetch_time()

        return pd.to_datetime(timestamp, unit="ms")

    except Exception:

        return pd.Timestamp.now()


# ===========================================================
# CONNECTION STATUS
# ===========================================================


def health_check():

    try:

        market.exchange.fetch_time()

        return {
            "status": "UP",
            "exchange": market.exchange.id,
            "server_time": str(get_server_time()),
        }

    except Exception as ex:

        return {"status": "DOWN", "message": str(ex)}


# ===========================================================
# CACHE
# ===========================================================


def clear_cache():

    market._cache.clear()


def cache_size():

    return len(market._cache)


# ===========================================================
# REFRESH
# ===========================================================


def refresh_market_data(symbol):

    clear_cache()

    get_current_price(symbol)

    get_open_interest(symbol)

    get_order_book(symbol)

    get_funding_rate(symbol)

    return True


# ===========================================================
# MARKET SUMMARY
# ===========================================================


def get_market_summary(symbol, timeframe="5m"):

    return {
        "snapshot": get_market_snapshot(symbol, timeframe),
        "price": get_current_price(symbol),
        "funding": get_funding_rate(symbol),
        "open_interest": get_open_interest(symbol),
        "orderbook": get_order_book(symbol),
    }


# ===========================================================
# SINGLETON EXPORT
# ===========================================================

MarketData = market


# ===========================================================
# TEST
# ===========================================================

if __name__ == "__main__":

    print(health_check())

    print(get_current_price("BTCUSDT"))
