from datetime import datetime, timedelta
from pathlib import Path

from backtracking.flow_backtracker import FlowBacktracker
from custom_types.rolling_time_window import RollingTimeWindow
from custom_types.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader
import time

DATA_DIR = Path("./datasets/")
DATA_DIR.mkdir(exist_ok=True)
loader = StockDataLoader(DATA_DIR)
loader.load("AAPL")
loader.load("XWD.TO")


def flow_backtrack(start, end, portfolio):
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    data_series, result_portfolio = backtracker.backtrack(portfolio, start, end)
    for i in range(100):
        data_series, result_portfolio = backtracker.backtrack(portfolio, start, end)
    print(f"Flow backtrack time: {time.time() - now}")
    return data_series, result_portfolio


def benchmark_backtrack():
    portfolio = Portfolio(positions={"XWD.TO": 0.5, "AAPL": 0.5})
    start = datetime.fromisoformat("2000-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")
    flow_backtrack(start, end, portfolio)


def benchmark_backtrack_with_rolling_window():
    portfolio = Portfolio(positions={"XWD.TO": 0.5, "AAPL": 0.5})
    start = datetime.fromisoformat("2000-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")
    window_size = timedelta(days=365)
    step_size = timedelta(days=1)
    print(
        f"Starting benchmark with rolling window: window size: {window_size}, step size: {step_size}"
    )

    r2 = rolling_window_backtrack_alternative(
        start, end, window_size, step_size, portfolio
    )
    r1 = rolling_window_backtrack(start, end, window_size, step_size, portfolio)


def rolling_window_backtrack(start, end, window_size, step_size, portfolio):
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    rolling_window = RollingTimeWindow(start, end, window_size, step_size)
    result = backtracker.rolling_backtrack(portfolio, rolling_window)

    print(f"Rolling window backtrack time: {time.time() - now}")

    return result


def rolling_window_backtrack_alternative(start, end, window_size, step_size, portfolio):
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    result = backtracker.rolling_backtrack(
        portfolio,
        rolling_window=RollingTimeWindow(start, end, window_size, step_size),
    )
    print(f"Rolling window alternative backtrack time: {time.time() - now}")
    return result


if __name__ == "__main__":
    benchmark_backtrack_with_rolling_window()
