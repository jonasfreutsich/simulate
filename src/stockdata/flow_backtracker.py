from datetime import datetime
from typing import Dict, List, Sequence, Tuple

from dataseries.data_series import DataPoint, DataSeries
from stockdata.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader


class FlowBacktracker:
    """A class to efficiently backtrack portfolio values over time using pre-calculated flows for each ticker.
    This class is designed to optimize the backtracking process by pre-calculating the flows for each ticker over a specified time range, allowing for faster portfolio value calculations during backtracking.
    Attributes:
        loader (StockDataLoader): The data loader for fetching stock data.
        timestamps (Sequence[datetime]): The list of timestamps within the specified time range.
        flows (Dict[str, Dict[datetime, float]]): A dictionary mapping each ticker to its corresponding flow values at each timestamp.
        start (datetime): The start timestamp for the backtracking period.
        end (datetime): The end timestamp for the backtracking period.
        tickers (Sequence[str]): The list of tickers to include in the backtracking.
    Methods:
        __init__: Initialize the FlowBacktracker with a data loader, time range, and tickers.
        _calculate_flows: Pre-calculate the flows for each ticker over the specified time range.
        backtrack: Backtrack the portfolio value over the specified time range using pre-calculated flows.
    """

    def __init__(
        self,
        loader: StockDataLoader,
        start: datetime,
        end: datetime,
        tickers: Sequence[str],
    ) -> None:
        """Initialize the FlowBacktracker with a data loader, time range, and tickers.
        Args:
            loader (StockDataLoader): The data loader for fetching stock data.
            start (datetime): The start timestamp for the backtracking period.
            end (datetime): The end timestamp for the backtracking period.
            tickers (Sequence[str]): The list of tickers to include in the backtracking.
        Raises:
            ValueError: If start is after end or if tickers are not unique."""
        if start > end:
            raise ValueError("Start must not be after end.")
        if len(tickers) != len(set(tickers)):
            raise ValueError("Tickers must be unique.")
        self.loader = loader
        self.timestamps: Sequence[datetime] = ()
        self.flows: Dict[str, Dict[datetime, float]] = {}
        self.start = start
        self.end = end
        self.tickers = tickers
        self._calculate_flows()

    def _calculate_flows(self) -> None:
        """Pre-calculate the flows for each ticker over the specified time range.
        Raises:
            ValueError: If valid starting prices cannot be determined for any ticker.
        """
        series_by_ticker = {ticker: self.loader.load(ticker) for ticker in self.tickers}

        # Pre-calculate the common timestamps that fall within the specified range
        self.timestamps = [
            timestamp
            for timestamp in DataSeries.common_timeline(series_by_ticker.values())
            if (self.start <= timestamp and timestamp <= self.end)
        ]
        if not self.timestamps:
            self.flows = {ticker: {} for ticker in self.tickers}
            return  # Early return if there are no timestamps in the range

        last_price_points = {
            ticker: series.before(self.timestamps[0])
            for ticker, series in series_by_ticker.items()
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
                f"{', '.join(invalid_start_prices)} at {self.timestamps[0]}"
            )
        # Pre-calculate the last prices for each ticker at the start of the backtracking period
        last_prices = {
            ticker: datapoint.value
            for ticker, datapoint in last_price_points.items()
            if datapoint is not None
        }
        # Pre-calculate the flows for each ticker at each timestamp
        self.flows = {}
        for ticker in self.tickers:
            ticker_flows = {}
            for timestamp in self.timestamps:
                price = series_by_ticker[ticker].value_at(timestamp)
                # Check for invalid price values
                if price <= 0:
                    raise ValueError(
                        f"Could not determine a valid price for {ticker} "
                        f"at {timestamp}: {price}"
                    )
                # Calculate the flow for this timestamp
                ticker_flows[timestamp] = price / last_prices[ticker]
                # Update the last price for the next iteration
                last_prices[ticker] = price
            self.flows[ticker] = ticker_flows

    def backtrack(
        self,
        portfolio: Portfolio,
        start: datetime,
        end: datetime,
    ) -> Tuple[DataSeries, Portfolio]:
        """Backtrack the portfolio value over the specified time range using pre-calculated flows.
        Args:
            portfolio (Portfolio): The initial portfolio to backtrack.
            start (datetime): The start timestamp for backtracking.
            end (datetime): The end timestamp for backtracking.
            Returns:
                Tuple[DataSeries, Portfolio]: A tuple containing the backtracked data series and the updated portfolio.
        """
        if start > end:
            raise ValueError("Start must not be after end.")
        if start < self.start or self.end < end:
            raise ValueError(
                "Start and End are outisde of the valid range of this tracker."
            )

        positions = tuple(portfolio.get_positions())

        # Check if all tickers in the portfolio are configured for this tracker
        for ticker in positions:
            if ticker not in self.tickers:
                raise ValueError(f"{ticker} is not configured for this tracker.")
        updated_portfolio = portfolio.copy()
        points = []

        # Iterate over the timestamps in the specified range
        for timestamp in filter(lambda ts: start < ts <= end, self.timestamps):
            update: Dict[str, float] = {}
            # Update the portfolio based on the pre-calculated flows for each ticker
            for ticker in positions:
                update[ticker] = self.flows[ticker][timestamp]

            updated_portfolio.update(update)
            # Append the current timestamp and portfolio value to results
            points.append(
                DataPoint(
                    timestamp,
                    updated_portfolio.get_value(),
                )
            )
            # If the portfolio has crashed (value is effectively zero), we stop the backtracking
            if updated_portfolio.is_crashed():
                break

        return DataSeries(points), updated_portfolio
