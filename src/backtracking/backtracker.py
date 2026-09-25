from datetime import datetime
from typing import Tuple


from dataseries.data_series import DataPoint, DataSeries
from stockdata.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader


class Backtracker:
    """A class to backtrack portfolio values over time using stock data.
    This class is designed to backtrack the value of a portfolio over a specified time range by fetching stock data for each ticker in the portfolio and calculating the portfolio value at each timestamp.
    Attributes:
        loader (StockDataLoader): The data loader for fetching stock data.
    Methods:
        __init__: Initialize the Backtracker with a data loader.
        backtrack: Backtrack the portfolio value over the specified time range.
    """

    def __init__(self, loader: StockDataLoader) -> None:
        self.loader = loader

    def backtrack(
        self,
        portfolio: Portfolio,
        start: datetime,
        end: datetime,
    ) -> Tuple[DataSeries, Portfolio]:
        """Backtrack the portfolio value over the specified time range.
        Args:
        portfolio (Portfolio): The initial portfolio to backtrack.
        start (datetime): The start timestamp for backtracking.
        end (datetime): The end timestamp for backtracking.
        Returns:
            Tuple[DataSeries, Portfolio]: A tuple containing the backtracked data series and the updated portfolio.
        Raises:
            ValueError: If start is after end or if valid starting prices cannot be determined for any ticker.
        """
        series_by_ticker = {
            ticker: self.loader.load(ticker) for ticker in portfolio.get_positions()
        }
        # Pre-calculate the common timestamps that fall within the specified range
        timestamps = DataSeries.common_timeline(series_by_ticker.values())

        if not timestamps:
            return (
                DataSeries(),
                portfolio.copy(),
            )  # Early return if there are no timestamps in the range

        starting_positions = portfolio.get_positions()
        last_price_points = {
            ticker: series.after(start) for ticker, series in series_by_ticker.items()
        }
        invalid_start_prices = [
            ticker
            for ticker, datapoint in last_price_points.items()
            if datapoint is None or datapoint.value <= 0
        ]
        # If there are any tickers with invalid starting prices, raise an error
        if invalid_start_prices:
            raise ValueError(
                "Could not determine valid starting prices for "
                f"{', '.join(invalid_start_prices)} at {start}"
            )
        # Pre-calculate the last prices for each ticker at the start of the backtracking period
        last_prices = {
            ticker: datapoint.value
            for ticker, datapoint in last_price_points.items()
            if datapoint is not None
        }

        points = []
        result_portfolio = portfolio.copy()
        # Iterate through the timestamps in the specified range and update the portfolio value based on stock price changes
        for timestamp in filter(lambda ts: start < ts <= end, timestamps):
            changes = {}
            for ticker in starting_positions:
                price = series_by_ticker[ticker].value_at(timestamp)
                # Check for invalid price values
                if price <= 0:
                    raise ValueError(
                        f"Could not determine a valid price for {ticker} "
                        f"at {timestamp}: {price}"
                    )
                # Calculate the change in price relative to the last known price and update the last price for the next iteration
                changes[ticker] = price / last_prices[ticker]
                last_prices[ticker] = price

            result_portfolio.update(changes)

            points.append(
                DataPoint(
                    timestamp,
                    result_portfolio.get_value(),
                )
            )
            # stop if value is effectively zero
            if result_portfolio.is_crashed():
                break

        return DataSeries(points), result_portfolio
