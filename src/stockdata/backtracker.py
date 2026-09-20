from datetime import datetime
from threading import currentThread

from curl_cffi import CurlECode

from dataseries.data_series import DataPoint, DataSeries
from stockdata.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader


class Backtracker:

    def __init__(self, loader: StockDataLoader) -> None:
        self.loader = loader

    def backtrack(
        self,
        portfolio: Portfolio,
        start: datetime,
        end: datetime,
    ) -> DataSeries:

        series_by_ticker = {
            ticker: self.loader.load(ticker) for ticker in portfolio.get_positions()
        }

        timestamps = sorted(
            {
                point.timestamp
                for series in series_by_ticker.values()
                for point in series.between(start, end)
            }
        )

        if not timestamps:
            return DataSeries()

        starting_positions = portfolio.get_positions()

        last_prices = {
            ticker: series.before(start) for ticker, series in series_by_ticker.items()
        }

        if any(
            datapoint is None or datapoint.value <= 0
            for datapoint in last_prices.values()
        ):
            raise ValueError(f"Could not determine valid starting prices at {start}")
        last_prices = {ticker: dp.value for ticker, dp in last_prices.items()}  # type: ignore
        points = []

        current_portfolio = Portfolio(portfolio.get_positions())

        for timestamp in timestamps:
            changes = {}

            for ticker in starting_positions:
                price = series_by_ticker[ticker].value_at(timestamp)

                changes[ticker] = price / last_prices[ticker]
                last_prices[ticker] = price

            current_portfolio.update(changes)

            points.append(
                DataPoint(
                    timestamp,
                    current_portfolio.get_value(),
                )
            )

            if current_portfolio.is_crashed():
                break

        return DataSeries(points)
