from datetime import datetime
from pathlib import Path
from typing import Dict


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio import Portfolio
from custom_types.time_series_snapshot import TimeSeriesSnapshot
from performance.performance_parameters import (
    FiveYearPerformanceParameters,
    OneYearMonthlyGrainPerformanceParameters,
    OneYearPerformanceParameters,
)
from performance.performance_reporter import PerformanceReporter
from performance.portfolio_metric import (
    global_metrics,
)
from stockdata.stock_data_loader import StockDataLoader
import time
from performance.events.event import global_events

DATA_DIR = Path("./datasets/")
DATA_DIR.mkdir(exist_ok=True)
loader = StockDataLoader(DATA_DIR)
loader.load("AAPL")
loader.load("XWD.TO")


def flow_backtrack(start, end, portfolio) -> TimeSeriesSnapshot:
    now = time.time()
    backtracker = FlowBacktracker(loader, TimeWindow(start, end), portfolio=portfolio)
    result = backtracker.backtrack(TimeWindow(start, end))
    print(f"Flow backtrack time: {time.time() - now}")
    return result


def test_performance():
    portfolioA = Portfolio(positions={"XWD.TO": 0.5, "AAPL": 0.5})
    portfolioB = Portfolio(positions={"XWD.TO": 1})
    portfolios = {portfolioA, portfolioB}
    tickers = {ticker for portfolio in portfolios for ticker in portfolio}
    start = datetime.fromisoformat("2000-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")

    # Five Year Performance
    performance = OneYearMonthlyGrainPerformanceParameters(
        start=start, end=end, events=global_events, metrics=global_metrics
    ).build(loader, tickers)
    PerformanceReporter.print(performance, portfolios)
    # One Year Performance
    performance = OneYearPerformanceParameters(
        start=start, end=end, events=global_events, metrics=global_metrics
    ).build(loader, tickers)
    PerformanceReporter.print(performance, portfolios)


def rolling_window_backtrack(
    start, end, window_size, step_size, portfolio
) -> Dict[TimeWindow, TimeSeriesSnapshot]:
    now = time.time()
    backtracker = FlowBacktracker(loader, TimeWindow(start, end), portfolio)
    rolling_window = RollingTimeWindow(start, end, window_size, step_size)
    result = backtracker.rolling_backtrack(rolling_window)

    print(f"Rolling window backtrack time: {time.time() - now}")

    return result


if __name__ == "__main__":
    test_performance()
