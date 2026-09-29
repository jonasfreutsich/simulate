from datetime import datetime, timedelta

import pytest

from backtracking.flow_backtracker import FlowBacktracker
from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from dataseries.data_series import DataPoint, DataSeries
from stockdata.stock_data_loader import StockDataLoader

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def dt(day: int) -> datetime:
    return datetime(2020, 1, 1) + timedelta(days=day)


class InMemoryStockDataLoader(StockDataLoader):
    def __init__(self, series_by_ticker: dict[str, DataSeries]):
        self.series_by_ticker = series_by_ticker

    def load(self, ticker: str) -> DataSeries:
        return self.series_by_ticker[ticker]


def series(*values: float) -> DataSeries:
    return DataSeries(DataPoint(dt(i), value) for i, value in enumerate(values))


@pytest.fixture
def loader() -> InMemoryStockDataLoader:
    """
    Prices:

        A:
            t0 = 100
            t1 = 110
            t2 = 100
            t3 = 120
            t4 =  60

        B:
            t0 = 200
            t1 = 220
            t2 = 200
            t3 = 180
            t4 =  90

    Each series also contains a price at t=-1, which is used to
    calculate the flow at t=0.
    """
    return InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(-1), 100.0),
                    (dt(0), 100.0),
                    (dt(1), 110.0),
                    (dt(2), 100.0),
                    (dt(3), 120.0),
                    (dt(4), 60.0),
                ]
            ),
            "B": DataSeries(
                [
                    (dt(-1), 200.0),
                    (dt(0), 200.0),
                    (dt(1), 220.0),
                    (dt(2), 200.0),
                    (dt(3), 180.0),
                    (dt(4), 90.0),
                ]
            ),
        }
    )


@pytest.fixture
def backtracker(loader: InMemoryStockDataLoader) -> FlowBacktracker:
    return FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(0), dt(4)),
        tickers={"A", "B"},
    )


# ---------------------------------------------------------------------------
# TimeWindow
# ---------------------------------------------------------------------------


def test_time_window_contains_datetime():
    window = TimeWindow(dt(1), dt(3))

    assert dt(1) in window
    assert dt(2) in window
    assert dt(3) in window
    assert dt(0) not in window
    assert dt(4) not in window


def test_time_window_contains_nested_window():
    outer = TimeWindow(dt(0), dt(4))

    assert TimeWindow(dt(0), dt(4)) in outer
    assert TimeWindow(dt(1), dt(3)) in outer
    assert TimeWindow(dt(1), dt(4)) in outer
    assert TimeWindow(dt(0), dt(3)) in outer


def test_time_window_does_not_contain_overlapping_window():
    outer = TimeWindow(dt(1), dt(3))

    assert TimeWindow(dt(0), dt(2)) not in outer
    assert TimeWindow(dt(2), dt(4)) not in outer
    assert TimeWindow(dt(0), dt(4)) not in outer


def test_time_window_does_not_contain_unsupported_type():
    window = TimeWindow(dt(0), dt(4))

    assert "2020-01-01" not in window
    assert 1 not in window


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_rejects_invalid_tracker_range(loader):
    with pytest.raises(ValueError, match="start must be before end"):
        FlowBacktracker(
            loader=loader,
            window=TimeWindow(dt(4), dt(0)),
            tickers={"A", "B"},
        )


def test_tickers_are_stored(loader):
    tracker = FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(0), dt(4)),
        tickers={"A", "B"},
    )

    assert tracker.tickers == {"A", "B"}


def test_portfolio_tickers_override_configured_tickers(loader):
    portfolio = Portfolio({"A": 100.0})

    tracker = FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(0), dt(4)),
        tickers={"A", "B"},
        portfolio=portfolio,
    )

    assert tracker.tickers == {"A"}


# ---------------------------------------------------------------------------
# Flow calculation
# ---------------------------------------------------------------------------


def test_calculates_expected_flows(backtracker):
    assert backtracker.flows["A"] == {
        dt(0): 1.0,
        dt(1): 1.1,
        dt(2): 100.0 / 110.0,
        dt(3): 1.2,
        dt(4): 0.5,
    }

    assert backtracker.flows["B"] == {
        dt(0): 1.0,
        dt(1): 1.1,
        dt(2): 200.0 / 220.0,
        dt(3): 0.9,
        dt(4): 0.5,
    }


def test_flow_calculation_uses_price_before_tracker_start(loader):
    loader = InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(-1), 50.0),
                    (dt(0), 100.0),
                    (dt(1), 150.0),
                ]
            )
        }
    )

    tracker = FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(0), dt(1)),
        tickers={"A"},
    )

    assert tracker.flows["A"][dt(0)] == 2.0
    assert tracker.flows["A"][dt(1)] == 1.5


def test_rejects_missing_starting_price():
    loader = InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(1), 100.0),
                    (dt(2), 110.0),
                ]
            )
        }
    )

    with pytest.raises(
        ValueError,
        match="Could not determine valid starting prices for ",
    ):
        FlowBacktracker(
            loader=loader,
            window=TimeWindow(dt(0), dt(2)),
            tickers={"A"},
        )


@pytest.mark.parametrize("invalid_price", [0.0, -1.0])
def test_rejects_invalid_starting_price(loader, invalid_price):
    loader = InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(-1), 100.0),
                    (dt(0), invalid_price),
                ]
            )
        }
    )

    with pytest.raises(
        ValueError,
        match="Could not determine valid starting prices for A",
    ):
        FlowBacktracker(
            loader=loader,
            window=TimeWindow(dt(0), dt(1)),
            tickers={"A"},
        )


@pytest.mark.parametrize("invalid_price", [0.0, -1.0])
def test_rejects_invalid_price_after_start(loader, invalid_price):
    loader = InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(-1), 100.0),
                    (dt(0), 100.0),
                    (dt(1), invalid_price),
                ]
            )
        }
    )

    with pytest.raises(
        ValueError,
        match="Could not determine a valid price for A",
    ):
        FlowBacktracker(
            loader=loader,
            window=TimeWindow(dt(0), dt(1)),
            tickers={"A"},
        )


def test_empty_tracker_range_produces_empty_flows(loader):
    tracker = FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(5), dt(6)),
        tickers={"A", "B"},
    )

    assert tracker.flows == {
        "A": {},
        "B": {},
    }
    assert tracker.timestamps == ()


# ---------------------------------------------------------------------------
# backtrack_window
# ---------------------------------------------------------------------------


def test_backtrack_window_applies_flows(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        TimeWindow(dt(0), dt(3)),
        portfolio,
    )

    assert len(snapshot.series) == 3
    assert int(snapshot.series.value_at(dt(1))) == 110
    assert int(snapshot.series.value_at(dt(2))) == 100
    assert int(snapshot.series.value_at(dt(3))) == 120

    assert snapshot.final_portfolio == Portfolio({"A": 120.0})


def test_backtrack_window_does_not_include_start_timestamp(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        TimeWindow(dt(1), dt(3)),
        portfolio,
    )

    assert [point.timestamp for point in snapshot.series] == [
        dt(2),
        dt(3),
    ]


def test_backtrack_window_includes_end_timestamp(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        TimeWindow(dt(1), dt(3)),
        portfolio,
    )

    assert snapshot.end_timestamp == dt(3)


def test_backtrack_window_does_not_mutate_original_portfolio(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        TimeWindow(dt(0), dt(3)),
        portfolio,
    )

    assert portfolio == Portfolio({"A": 100.0})
    assert snapshot.final_portfolio != portfolio


# ---------------------------------------------------------------------------
# backtrack
# ---------------------------------------------------------------------------


def test_backtrack_delegates_to_backtrack_window(backtracker):
    portfolio = Portfolio({"A": 100.0, "B": 100.0})
    window = TimeWindow(dt(1), dt(4))

    actual = backtracker.backtrack(window, portfolio)
    expected = backtracker.backtrack_window(window, portfolio)

    assert len(actual) == len(expected)
    assert int(100 * actual.final_value) == int(100 * expected.final_value)


def test_backtrack_uses_default_portfolio(backtracker):
    portfolio = Portfolio({"A": 100.0})

    tracker = FlowBacktracker(
        loader=backtracker.loader,
        window=backtracker.time_range,
        tickers={"A"},
        portfolio=portfolio,
    )

    snapshot = tracker.backtrack(TimeWindow(dt(0), dt(2)))

    assert snapshot.final_portfolio == Portfolio({"A": 100.0})


def test_backtrack_rejects_window_outside_tracker(backtracker):
    with pytest.raises(ValueError, match="valid time range"):
        backtracker.backtrack(
            TimeWindow(dt(-1), dt(2)),
            Portfolio({"A": 100.0}),
        )

    with pytest.raises(ValueError, match="valid time range"):
        backtracker.backtrack(
            TimeWindow(dt(2), dt(5)),
            Portfolio({"A": 100.0}),
        )


def test_backtrack_rejects_unknown_ticker(backtracker):
    with pytest.raises(ValueError, match="C is not configured"):
        backtracker.backtrack(
            TimeWindow(dt(0), dt(2)),
            Portfolio({"C": 100.0}),
        )


def test_backtrack_requires_portfolio(backtracker):
    with pytest.raises(ValueError, match="must specify a portfolio"):
        backtracker.backtrack(TimeWindow(dt(0), dt(2)))


# ---------------------------------------------------------------------------
# Rolling windows
# ---------------------------------------------------------------------------


@pytest.fixture
def rolling_window() -> RollingTimeWindow:
    return RollingTimeWindow(
        start=dt(0),
        end=dt(4),
        window_size=timedelta(days=2),
        step_size=timedelta(days=1),
    )


def test_rolling_backtrack_returns_expected_windows(
    backtracker,
    rolling_window,
):
    portfolio = Portfolio({"A": 100.0})

    result = backtracker.rolling_backtrack(
        rolling_window,
        portfolio,
    )

    expected_windows = [
        TimeWindow(dt(0), dt(2)),
        TimeWindow(dt(1), dt(3)),
        TimeWindow(dt(2), dt(4)),
    ]

    assert list(result.keys()) == expected_windows


def test_rolling_backtrack_matches_individual_backtracks(
    backtracker,
    rolling_window,
):
    portfolio = Portfolio({"A": 100.0, "B": 100.0})

    rolling_result = backtracker.rolling_backtrack(
        rolling_window,
        portfolio,
    )

    for window in rolling_window:
        expected = backtracker.backtrack(window, portfolio)
        actual = rolling_result[window]

        assert DataSeries.is_close(actual.series, expected.series)
        assert actual.final_portfolio == expected.final_portfolio


def test_rolling_backtrack_does_not_mutate_input_portfolio(
    backtracker,
    rolling_window,
):
    portfolio = Portfolio({"A": 100.0})

    backtracker.rolling_backtrack(
        rolling_window,
        portfolio,
    )

    assert portfolio == Portfolio({"A": 100.0})


def test_rolling_backtrack_rejects_window_outside_tracker(backtracker):
    rolling_window = RollingTimeWindow(
        start=dt(-1),
        end=dt(4),
        window_size=timedelta(days=2),
        step_size=timedelta(days=1),
    )

    with pytest.raises(ValueError, match="valid time range"):
        backtracker.rolling_backtrack(
            rolling_window,
            Portfolio({"A": 100.0}),
        )


def test_rolling_backtrack_requires_portfolio(
    backtracker,
    rolling_window,
):
    with pytest.raises(ValueError, match="must specify a portfolio"):
        backtracker.rolling_backtrack(rolling_window)


# ---------------------------------------------------------------------------
# Crash behavior
# ---------------------------------------------------------------------------


def test_backtrack_stops_after_portfolio_crashes():
    loader = InMemoryStockDataLoader(
        {
            "A": DataSeries(
                [
                    (dt(-1), 100.0),
                    (dt(0), 100.0),
                    (dt(1), 1e-7),
                    (dt(2), 100.0),
                    (dt(3), 200.0),
                ]
            )
        }
    )

    tracker = FlowBacktracker(
        loader=loader,
        window=TimeWindow(dt(0), dt(3)),
        tickers={"A"},
    )

    snapshot = tracker.backtrack(
        TimeWindow(dt(0), dt(3)),
        Portfolio({"A": 100.0}),
    )

    assert len(snapshot) == 1
    assert snapshot.end_timestamp == dt(1)
    assert snapshot.crashed


# ---------------------------------------------------------------------------
# Boundary behavior
# ---------------------------------------------------------------------------


def test_window_start_between_data_points(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        TimeWindow(
            dt(1) + timedelta(hours=12),
            dt(3),
        ),
        portfolio,
    )

    assert [point.timestamp for point in snapshot.series] == [
        dt(2),
        dt(3),
    ]


# ---------------------------------------------------------------------------
# Multiple positions
# ---------------------------------------------------------------------------


def test_backtrack_updates_each_position_independently(backtracker):
    portfolio = Portfolio(
        {
            "A": 100.0,
            "B": 100.0,
        }
    )

    snapshot = backtracker.backtrack(
        TimeWindow(dt(0), dt(3)),
        portfolio,
    )

    # A: 100 -> 110 -> 100 -> 120
    # B: 100 -> 110 -> 100 -> 90
    assert snapshot.final_portfolio == Portfolio(
        {
            "A": 120.0,
            "B": 90.0,
        }
    )
