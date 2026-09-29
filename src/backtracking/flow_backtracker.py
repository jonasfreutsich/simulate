from bisect import bisect_right
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Set


from custom_types.time_series_snapshot import TimeSeriesSnapshot
from dataseries.data_series import DataPoint, DataSeries
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio import Portfolio
from stockdata.stock_data_loader import StockDataLoader


class FlowBacktracker:
    """Backtrack portfolio values using precomputed per-ticker price flows.

    During initialization, price-change factors are calculated for each
    configured ticker at each common timestamp in the configured time range.
    Backtracking then applies these factors to a portfolio without requiring
    additional market-data lookups.

    Attributes:
        loader: Data loader used to retrieve historical price series.
        timestamps: Sorted timestamps at which flows are available.
        flows: Mapping of ticker -> timestamp -> multiplicative price change.
        time_range: Time range covered by the precomputed flows.
        tickers: Tickers for which flows have been calculated.
        portfolio: Default portfolio used when none is supplied to
            ``backtrack()`` or ``rolling_backtrack()``.
    """

    def __init__(
        self,
        loader: StockDataLoader,
        window: TimeWindow,
        tickers: Optional[Set[str]] = None,
        portfolio: Optional[Portfolio] = None,
    ) -> None:
        """Initialize the FlowBacktracker with a data loader, time range, and tickers.
        Args:
            loader (StockDataLoader): The data loader for fetching stock data.
            window (TimeWindow): datetime range used to limit ticker data and validating input windows for backtracking.
            tickers (Set[str]): The set of tickers to include in the backtracking. If portfolio s specified, this will be overwritten by the key set of portfolio.
            portfolio (Optional[Portfolio]): Initial portfolio to backtrack.
        """

        self.loader: StockDataLoader = loader
        self.timestamps: Sequence[datetime] = ()
        self.flows: Dict[str, Dict[datetime, float]] = {}
        self.time_range: TimeWindow = window
        if portfolio is None and tickers is None:
            raise ValueError("tickers and portfolio must not both be None.")
        self.tickers: Set[str] = (
            set(tickers or set()) if portfolio is None else set(iter(portfolio))
        )
        if not self.tickers:
            raise ValueError("Input parameters did not contain any tickers!")
        self.portfolio: Optional[Portfolio] = portfolio
        self._calculate_flows()

    def _calculate_flows(self) -> None:
        """Pre-calculate the flows for each ticker over the specified time range.
        Raises:
            ValueError: If any ticker has no valid starting price.
            ValueError: If any ticker has a non-positive price within the time range.
        """
        series_by_ticker = {ticker: self.loader.load(ticker) for ticker in self.tickers}

        # Pre-calculate the common timestamps that fall within the specified range
        self.timestamps = tuple(
            timestamp
            for timestamp in DataSeries.common_timeline(series_by_ticker.values())
            if timestamp in self.time_range
        )
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

        assert all(dp is not None for dp in last_price_points.values())
        # Pre-calculate the last prices for each ticker at the start of the backtracking period
        last_prices = {
            ticker: datapoint.value
            for ticker, datapoint in last_price_points.items()
            if datapoint is not None
        }
        # Pre-calculate the flows for each ticker at each timestamp
        self.flows = {}
        for ticker, series in series_by_ticker.items():
            ticker_flows = {}
            for datapoint in series.iter_at(self.timestamps):
                price = datapoint.value
                timestamp = datapoint.timestamp
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
        self, window: TimeWindow, portfolio: Optional[Portfolio] = None
    ) -> TimeSeriesSnapshot:
        """Backtrack the portfolio value over the specified time range using pre-calculated flows.
        Args:
            window (TimeWindow): Backtrack window.
            ortfolio (Portfolio): The initial portfolio to backtrack.
        Returns:
                TimeSeriesSnapshot: A snapshot containing the backtracked data series and the updated portfolio.
        Raises:
            ValueError: If window is outside the valid range of this tracker.
            ValueError: If any ticker in the portfolio is not configured for this tracker.
        """
        # validate window
        if window.start < self.time_range.start or self.time_range.end < window.end:
            raise ValueError(
                "Window parameter is not in the valid time range of the tracker."
            )
        if portfolio is not None:
            self._validate_portfolio(portfolio)
            backtracking_portfolio = portfolio
        else:
            backtracking_portfolio = self.portfolio

        if backtracking_portfolio is None:
            raise ValueError(
                "The backtracker was not initialized with a portfolio, you must specify a portfolio."
            )

        return self.backtrack_window(
            window,
            backtracking_portfolio,
        )

    def rolling_backtrack(
        self,
        rolling_window: RollingTimeWindow,
        portfolio: Optional[Portfolio] = None,
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

        if portfolio is not None:
            self._validate_portfolio(portfolio)
            backtrack_portfolio = portfolio
        else:
            backtrack_portfolio = self.portfolio

        if backtrack_portfolio is None:
            raise ValueError(
                "The backtracker was not initialized with a portfolio, you must specify a portfolio."
            )
        if rolling_window.get_range() not in self.time_range:
            raise ValueError(
                "Provided rolling_window is not within the valid time range of the backtracker."
            )

        result: Dict[TimeWindow, TimeSeriesSnapshot] = {}

        for window in rolling_window:
            result[window] = self.backtrack_window(window, backtrack_portfolio)

        return result

    def backtrack_window(
        self, window: TimeWindow, portfolio: Portfolio
    ) -> TimeSeriesSnapshot:
        """Backtrack a portfolio over a time window.

        The portfolio state at ``window.start`` is treated as the initial state.
        Flow updates are applied for timestamps strictly after ``window.start``
        and up to and including ``window.end``.

        Args:
            window: The time window for backtracking. The caller must ensure that
                it is contained within the tracker's configured time range.
            portfolio: The initial portfolio state. The caller must ensure that
                all portfolio tickers are configured for the tracker.

        Returns:
            A snapshot containing the initial portfolio, the resulting time series,
            and the final portfolio state.
        """
        start_index = bisect_right(self.timestamps, window.start)
        end_index = bisect_right(self.timestamps, window.end)

        # filter flow tickers to those present in porfolio
        relevant_tickers = tuple(ticker for ticker in self.flows if ticker in portfolio)
        updated_portfolio = portfolio.copy()
        points: List[DataPoint] = []

        for timestamp in self.timestamps[start_index:end_index]:
            if updated_portfolio.is_crashed():
                break

            update = {
                ticker: self.flows[ticker][timestamp] for ticker in relevant_tickers
            }

            updated_portfolio.flow(update)

            points.append(
                DataPoint(
                    timestamp,
                    updated_portfolio.get_value(),
                )
            )
        return TimeSeriesSnapshot(portfolio, DataSeries(points), updated_portfolio)

    def _validate_portfolio(self, portfolio: Portfolio) -> None:
        for ticker in portfolio:
            if ticker not in self.tickers:
                raise ValueError(f"{ticker} is not configured for this tracker.")
