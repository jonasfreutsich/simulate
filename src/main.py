from datetime import datetime
from pathlib import Path

from stockdata.backtracker import Backtracker
from stockdata.flow_backtracker import FlowBacktracker
from stockdata.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader
import time

DATA_DIR = Path("./datasets/")
DATA_DIR.mkdir(exist_ok=True)
loader = StockDataLoader(DATA_DIR)
loader.load("AAPL")
loader.load("XWD.TO")


def normal_backtrack(start, end, portfolio):
    now = time.time()
    backtracker = Backtracker(loader)
    for i in range(100):
        backtracker.backtrack(
            portfolio,
            start,
            end,
        )
    print(f"Normal backtrack time: {time.time() - now}")


def flow_backtrack(start, end, portfolio):
    now = time.time()
    backtracker = FlowBacktracker(
        loader, start, end, list(portfolio.get_positions().keys())
    )
    for i in range(100):
        backtracker.backtrack(portfolio, start, end)
    print(f"Flow backtrack time: {time.time() - now}")


if __name__ == "__main__":
    portfolio = Portfolio(positions={"XWD.TO": 0.5, "AAPL": 0.5})
    start = datetime.fromisoformat("2000-01-01T20:00:00+00:00")
    end = datetime.fromisoformat("2026-09-20T20:00:00+00:00")
    normal_backtrack(start, end, portfolio)
    flow_backtrack(start, end, portfolio)
