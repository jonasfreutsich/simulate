from datetime import datetime
from pathlib import Path

from stockdata.backtracker import Backtracker
from stockdata.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader

DATA_DIR = Path("./datasets/")
DATA_DIR.mkdir(exist_ok=True)
loader = StockDataLoader(DATA_DIR)
backtracker = Backtracker(loader)

if __name__ == "__main__":
    portfolio = Portfolio(positions={"AAPL": 1})
    ds = backtracker.backtrack(
        portfolio,
        datetime.fromisoformat("2026-01-01T20:00:00+00:00"),
        datetime.fromisoformat("2026-09-20T20:00:00+00:00"),
    )
    print(ds[-1].value)
