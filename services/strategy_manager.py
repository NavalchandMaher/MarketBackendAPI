from services.signal_engine import generate_signal

def run_strategy(symbol):

    signal = generate_signal(symbol)

    return {
        "symbol": symbol,
        "signal": signal
    }