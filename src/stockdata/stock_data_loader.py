from pathlib import Path

import pandas as pd

from dataseries.data_series import DataPoint, DataSeries


class StockDataLoader:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def load(self, ticker: str) -> DataSeries:
        path = self._data_dir / f"{ticker}.parquet"

        if not path.exists():
            raise FileNotFoundError(f"No data file found for ticker '{ticker}': {path}")

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

        return DataSeries(points)
