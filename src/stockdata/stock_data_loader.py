from pathlib import Path
from typing import Dict

import pandas as pd

from dataseries.data_series import DataPoint, DataSeries
from stockdata.yfinance_api import YFinanceAPI


class StockDataLoader:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self.data: Dict[str, DataSeries] = {}

    def get_ticker_path(self, ticker: str) -> Path:
        return self._data_dir / f"{ticker}.parquet"

    def load(self, ticker: str) -> DataSeries:
        if ticker in self.data:
            return self.data[ticker]

        path = self.get_ticker_path(ticker)

        if not path.exists():
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
                    timestamp.to_pydatetime()  # type: ignore
                    if hasattr(timestamp, "to_pydatetime")
                    else timestamp
                ),
                value=float(close),
            )
            for timestamp, close in data["Close"].items()
            if pd.notna(close)
        ]

        self.data[ticker] = DataSeries(points)
        return self.data[ticker]
