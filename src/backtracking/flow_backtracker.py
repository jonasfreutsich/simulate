from bisect import bisect_right
from datetime import datetime
from typing import Dict, List, Sequence

from custom_types.time_series_snapshot import TimeSeriesSnapshot
from dataseries.data_series import DataPoint, DataSeries
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio import Portfolio
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
        self.tickers = tuple(tickers)
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
                # Flow represents the multiplicative price change since the previous timestamp.
                ticker_flows[timestamp] = price / last_prices[ticker]
                # Update the last price for the next iteration
                last_prices[ticker] = price
            self.flows[ticker] = ticker_flows

    def backtrack(
        self,
        portfolio: Portfolio,
        start: datetime,
        end: datetime,
    ) -> TimeSeriesSnapshot:
        """Backtrack the portfolio value over the specified time range using pre-calculated flows.
        Args:
            portfolio (Portfolio): The initial portfolio to backtrack.
            start (datetime): The start timestamp for backtracking.
            end (datetime): The end timestamp for backtracking.
        Returns:
                TimeSeriesSnapshot: A snapshot containing the backtracked data series and the updated portfolio.
        Raises:
            ValueError: If the start or end timestamps are outside the valid range of this tracker.
            ValueError: If any ticker in the portfolio is not configured for this tracker.
        """
        for ticker in portfolio.get_positions():
            if ticker not in self.tickers:
                raise ValueError(f"{ticker} is not configured for this tracker.")

        return self.backtrack_window(
            portfolio,
            TimeWindow(start, end),
        )

    def rolling_backtrack(
        self,
        portfolio: Portfolio,
        rolling_window: RollingTimeWindow,
    ) -> Dict[TimeWindow, TimeSeriesSnapshot]:
        """Backtrack the portfolio value over a rolling time window using pre-calculated flows.

        Args:
            portfolio: The initial portfolio to backtrack.
            rolling_window: The rolling time window for backtracking.

        Returns:
            A dictionary mapping each time window to its backtracked data series
            and updated portfolio.
        Raises:
            ValueError: If the start or end of any window is outside the valid range of this tracker.
            ValueError: If any ticker in the portfolio is not configured for this tracker.
        """
        for ticker in portfolio.get_positions():
            if ticker not in self.tickers:
                raise ValueError(f"{ticker} is not configured for this tracker.")
        result: Dict[TimeWindow, TimeSeriesSnapshot] = {}

        for window in rolling_window:
            result[window] = self.backtrack_window(portfolio, window)

        return result

    def backtrack_window(
        self,
        portfolio: Portfolio,
        window: TimeWindow,
    ) -> TimeSeriesSnapshot:
        """Backtrack a portfolio from the state at window.start through window.end.
        Args:
            portfolio (Portfolio): The initial portfolio to backtrack.
            window (TimeWindow): The time window for backtracking.

        Returns:
            TimeSeriesSnapshot: A snapshot containing the backtracked data series and the updated portfolio.
        Raises:
            ValueError: If the start or end of the window is outside the valid range of this tracker.
            ValueError: If any ticker in the portfolio is not configured for this tracker.
        """

        if window.start < self.start or self.end < window.end:
            raise ValueError(
                "Start and End of the window are outside of the valid range of this tracker."
            )
        start_index = bisect_right(self.timestamps, window.start)
        end_index = bisect_right(self.timestamps, window.end)

        positions = tuple(portfolio.get_positions())
        updated_portfolio = portfolio.copy()
        points: List[DataPoint] = []

        for timestamp in self.timestamps[start_index:end_index]:
            if updated_portfolio.is_crashed():
                break

            update = {ticker: self.flows[ticker][timestamp] for ticker in positions}

            updated_portfolio.flow(update)

            points.append(
                DataPoint(
                    timestamp,
                    updated_portfolio.get_value(),
                )
            )
        return TimeSeriesSnapshot(DataSeries(points), updated_portfolio)
