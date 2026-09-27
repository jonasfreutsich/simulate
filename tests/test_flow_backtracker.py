from datetime import datetime, timedelta

import pytest
from backtracking.flow_backtracker import FlowBacktracker
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from dataseries.data_series import DataPoint, DataSeries
from custom_types.portfolio import Portfolio
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

    The first flow is calculated relative to the observation before t0.
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
        start=dt(0),
        end=dt(4),
        tickers=["A", "B"],
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_rejects_invalid_tracker_range(loader):
    with pytest.raises(ValueError, match="Start must not be after end"):
        FlowBacktracker(
            loader=loader,
            start=dt(4),
            end=dt(0),
            tickers=["A"],
        )


def test_rejects_duplicate_tickers(loader):
    with pytest.raises(ValueError, match="Tickers must be unique"):
        FlowBacktracker(
            loader=loader,
            start=dt(0),
            end=dt(4),
            tickers=["A", "A"],
        )


def test_tickers_are_stored_as_immutable_sequence(loader):
    tracker = FlowBacktracker(
        loader=loader,
        start=dt(0),
        end=dt(4),
        tickers=["A", "B"],
    )

    assert tracker.tickers == ("A", "B")


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
        start=dt(0),
        end=dt(1),
        tickers=["A"],
    )
    print(tracker.flows)
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

    with pytest.raises(ValueError, match="Could not determine valid starting prices"):
        FlowBacktracker(
            loader=loader,
            start=dt(0),
            end=dt(2),
            tickers=["A"],
        )


@pytest.mark.parametrize("invalid_price", [0.0, -1.0])
def test_rejects_invalid_price(loader, invalid_price):
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
        ValueError, match="Could not determine valid starting prices for A"
    ):
        FlowBacktracker(
            loader=loader,
            start=dt(0),
            end=dt(1),
            tickers=["A"],
        )


# ---------------------------------------------------------------------------
# backtrack_window
# ---------------------------------------------------------------------------


def test_backtrack_window_applies_flows(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snap = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(0), dt(3)),
    )
    assert len(snap.series) == 3
    assert int(snap.series.value_at(dt(1))) == 110
    assert int(snap.series.value_at(dt(2))) == 100
    assert int(snap.series.value_at(dt(3))) == 120

    assert snap.final_portfolio == Portfolio({"A": 120.0})


def test_backtrack_window_does_not_include_start_timestamp(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(1), dt(3)),
    )

    assert [point.timestamp for point in snapshot.series] == [
        dt(2),
        dt(3),
    ]


def test_backtrack_window_includes_end_timestamp(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(1), dt(3)),
    )

    assert snapshot.end_timestamp == dt(3)


def test_backtrack_window_does_not_mutate_original_portfolio(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snapshot = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(0), dt(3)),
    )

    assert portfolio == Portfolio({"A": 100.0})
    assert snapshot.final_portfolio != portfolio


def test_backtrack_window_with_start_equal_end(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snap = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(2), dt(2)),
    )

    assert len(snap) == 0
    assert snap.final_portfolio == portfolio


def test_backtrack_window_rejects_invalid_range(backtracker):
    with pytest.raises(ValueError, match="Start must not be after end"):
        backtracker.backtrack_window(
            Portfolio({"A": 100.0}),
            TimeWindow(dt(3), dt(2)),
        )


def test_backtrack_window_rejects_window_outside_tracker(backtracker):
    with pytest.raises(ValueError, match="outside of the valid range"):
        backtracker.backtrack_window(
            Portfolio({"A": 100.0}),
            TimeWindow(dt(-1), dt(2)),
        )

    with pytest.raises(ValueError, match="outside of the valid range"):
        backtracker.backtrack_window(
            Portfolio({"A": 100.0}),
            TimeWindow(dt(2), dt(5)),
        )


def test_backtrack_window_rejects_unknown_ticker(backtracker):
    with pytest.raises(ValueError, match="C is not configured"):
        backtracker.backtrack_window(
            Portfolio({"C": 100.0}),
            TimeWindow(dt(0), dt(2)),
        )


# ---------------------------------------------------------------------------
# backtrack
# ---------------------------------------------------------------------------


def test_backtrack_matches_backtrack_window(backtracker):
    portfolio = Portfolio({"A": 100.0, "B": 100.0})

    data1, result1 = backtracker.backtrack(
        portfolio,
        dt(1),
        dt(4),
    )

    data2, result2 = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(1), dt(4)),
    )

    assert data1 == data2
    assert result1 == result2


# ---------------------------------------------------------------------------
# Rolling windows
# ---------------------------------------------------------------------------


def test_rolling_backtrack_returns_expected_windows(backtracker):
    portfolio = Portfolio({"A": 100.0})

    rolling_window = RollingTimeWindow(
        start=dt(0),
        end=dt(4),
        window_size=timedelta(days=2),
        step_size=timedelta(days=1),
    )

    result = backtracker.rolling_backtrack(
        portfolio,
        rolling_window,
    )

    expected_windows = [
        TimeWindow(dt(0), dt(2)),
        TimeWindow(dt(1), dt(3)),
        TimeWindow(dt(2), dt(4)),
    ]

    assert list(result.keys()) == expected_windows


def test_rolling_backtrack_matches_individual_backtracks(backtracker):
    portfolio = Portfolio({"A": 100.0, "B": 100.0})

    rolling_window = RollingTimeWindow(
        start=dt(0),
        end=dt(4),
        window_size=timedelta(days=2),
        step_size=timedelta(days=1),
    )

    rolling_result = backtracker.rolling_backtrack(
        portfolio,
        rolling_window,
    )

    for window in rolling_window:
        expected_snap = backtracker.backtrack(
            portfolio,
            window.start,
            window.end,
        )

        actual_snap = rolling_result[window]

        assert DataSeries.is_close(actual_snap.series, expected_snap.series)
        assert actual_snap.final_portfolio == expected_snap.final_portfolio


def test_rolling_backtrack_does_not_mutate_input_portfolio(backtracker):
    portfolio = Portfolio({"A": 100.0})

    rolling_window = RollingTimeWindow(
        start=dt(0),
        end=dt(4),
        window_size=timedelta(days=2),
        step_size=timedelta(days=1),
    )

    backtracker.rolling_backtrack(portfolio, rolling_window)

    assert portfolio == Portfolio({"A": 100.0})


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
        start=dt(0),
        end=dt(3),
        tickers=["A"],
    )

    snap = tracker.backtrack(
        Portfolio({"A": 100.0}),
        dt(0),
        dt(3),
    )

    # The first update crashes the portfolio.
    assert len(snap) == 1
    assert snap.end_timestamp == dt(1)
    assert snap.crashed


# ---------------------------------------------------------------------------
# Boundary-focused regression tests for bisect_right
# ---------------------------------------------------------------------------


def test_window_boundary_semantics(backtracker):
    portfolio = Portfolio({"A": 100.0})

    snap = backtracker.backtrack_window(
        portfolio,
        TimeWindow(dt(1), dt(3)),
    )

    timestamps = [point.timestamp for point in snap.series]

    # start is exclusive, end is inclusive
    assert timestamps == [dt(2), dt(3)]


def test_window_start_between_data_points(backtracker):
    portfolio = Portfolio({"A": 100.0})

    # There is no timestamp at day 1.5.
    snap = backtracker.backtrack_window(
        portfolio,
        TimeWindow(
            dt(1) + timedelta(hours=12),
            dt(3),
        ),
    )

    assert [point.timestamp for point in snap.series] == [
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

    snap = backtracker.backtrack(
        portfolio,
        dt(0),
        dt(3),
    )

    # A: 100 -> 110 -> 100 -> 120
    # B: 100 -> 110 -> 100 -> 90
    assert snap.final_portfolio == Portfolio(
        {
            "A": 120.0,
            "B": 90.0,
        }
    )
