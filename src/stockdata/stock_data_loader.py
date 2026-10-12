from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict

import pandas as pd

from custom_types.dataseries.data_series import DataPoint, DataSeries
from stockdata.ticker_db import YTicker
from stockdata.yfinance_api import YFinanceAPI

logger = logging.getLogger("simulate")
instance = None


class StockDataLoader:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self.data: Dict[str, DataSeries] = {}

    def get_ticker_path(self, ticker: str) -> Path:
        return self._data_dir / f"{ticker}.parquet"

    def load(self, ticker: str) -> DataSeries:
        if ticker in self.data:
            logger.info(f"Loading ticker {ticker} from database.")
            return self.data[ticker]

        path = self.get_ticker_path(ticker)

        if not path.exists():
            logger.info(f"Loading ticker {ticker} from YFinanceAPI.")
            YFinanceAPI.download(ticker, path)
            if not path.exists():
                raise FileNotFoundError(
                    f"No data file found for ticker '{ticker}': {path}"
                )

        try:
            data = pd.read_parquet(path)
        except Exception as e:
            raise RuntimeError(f"Failed to read data for ticker '{ticker}': {e}") from e

        if "Close" not in data.columns:
            raise ValueError(
                f"Data file for '{ticker}' does not contain a 'Close' column."
            )

        points = [
            DataPoint(
                timestamp=(
                    self.normalize_datetime(timestamp.to_pydatetime())  # type: ignore
                    if hasattr(timestamp, "to_pydatetime")
                    else self.normalize_datetime(timestamp)  # type: ignore
                ),
                value=float(close),
            )
            for timestamp, close in data["Close"].items()
            if pd.notna(close)
        ]

        self.data[ticker] = DataSeries(points)
        return self.data[ticker]

    def save_info(self, path: Path):
        info = {}
        for ticker, series in self.data.items():
            yticker = YTicker(ticker)
            yticker.set_range(series.start().timestamp, series.end().timestamp)
            info[yticker.name] = str(yticker.range)
        path.write_text(json.dumps(info, indent=2))

    @staticmethod
    def normalize_datetime(date: datetime) -> datetime:
        return datetime(year=date.year, month=date.month, day=date.day)

    @staticmethod
    def get_instance():
        global instance
        DATA_DIR = Path("./datasets/")

        if instance is None:
            DATA_DIR.mkdir(exist_ok=True)
            instance = StockDataLoader(DATA_DIR)

        return instance
