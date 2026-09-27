from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from backtracking.flow_backtracker import FlowBacktracker
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio import Portfolio
from custom_types.time_series_snapshot import TimeSeriesSnapshot
from performance.events.event import NegativeReturnEvent
from performance.events.event_processor import EventProcessor
from performance.portfolio_metric import AnnualizedReturnMetric
from performance.portfolio_metric import ReturnMetric
from stockdata.stock_data_loader import StockDataLoader
import time

DATA_DIR = Path("./datasets/")
DATA_DIR.mkdir(exist_ok=True)
loader = StockDataLoader(DATA_DIR)
loader.load("AAPL")
loader.load("XWD.TO")


def flow_backtrack(start, end, portfolio) -> TimeSeriesSnapshot:
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    result = backtracker.backtrack(portfolio, start, end)
    print(f"Flow backtrack time: {time.time() - now}")
    return result


def benchmark_backtrack():
    portfolio = Portfolio(positions={"XWD.TO": 0.5, "AAPL": 0.5})
    start = datetime.fromisoformat("2026-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")
    result = flow_backtrack(start, end, portfolio)
    metric = AnnualizedReturnMetric().metric(result)
    print(metric)
    print(ReturnMetric().metric(result))


def test_event_eval():
    portfolio = Portfolio(positions={"XWD.TO": 1})
    start = datetime.fromisoformat("2000-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")
    window_size = timedelta(days=365 * 2)
    step_size = timedelta(days=365)

    event_processor = EventProcessor(events={"negative_return": NegativeReturnEvent()})

    print(
        f"Starting benchmark with rolling window: window size: {window_size}, step size: {step_size}"
    )
    snapshots = rolling_window_backtrack(start, end, window_size, step_size, portfolio)
    print(event_processor.evaluate_event_rates(snapshots))


def rolling_window_backtrack(
    start, end, window_size, step_size, portfolio
) -> Dict[TimeWindow, TimeSeriesSnapshot]:
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    rolling_window = RollingTimeWindow(start, end, window_size, step_size)
    result = backtracker.rolling_backtrack(portfolio, rolling_window)

    print(f"Rolling window backtrack time: {time.time() - now}")

    return result


if __name__ == "__main__":
    benchmark_backtrack()
