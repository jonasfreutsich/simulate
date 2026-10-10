from datetime import datetime
from typing import Dict

from matplotlib.dates import relativedelta


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.allocation.allocation_strategies import (
    FireStrategy,
    PeriodicContribution,
)
from custom_types.portfolio.portfolio_comparison import PortfolioComparison
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio.portfolio import Portfolio
from custom_types.dataseries.snapshot import TimeSeriesSnapshot
from custom_types.time_types import CalendarDelta, Period
from performance.performance_parameters import (
    FiveYearPerformanceParameters,
)
from performance.performance_reporter import PerformanceReporter
from performance.portfolio_metric import (
    global_metrics,
)
import time
from performance.events.event import global_events
from stockdata.stock_data_loader import StockDataLoader


def flow_backtrack(start, end) -> TimeSeriesSnapshot:
    now = time.time()
    portfolio = Portfolio(
        positions={"XWD.TO": 0.5, "AAPL": 0.5},
        strategy=PeriodicContribution(30, {"XWD.TO": 0.5, "AAPL": 0.5}),
    )
    backtracker = FlowBacktracker(
        StockDataLoader.get_instance(), TimeWindow(start, end), portfolio=portfolio
    )
    result = backtracker.backtrack(TimeWindow(start, end))
    print(f"Flow backtrack time: {time.time() - now}")
    print(result.initial_value)
    print(result.final_value)
    print(result.contributed_value)
    return result


def test_comparison():
    strategy = FireStrategy(Period.MONTHLY, 1, 4, relativedelta(years=4))
    portfolios = {
        Portfolio({"IWDA.AS": 1}),
        Portfolio({"XWD.TO": 1}),
    }
    comp = PortfolioComparison(portfolios)
    start = datetime.fromisoformat("2006-01-01")
    end = datetime.fromisoformat("2011-01-01")
    comp.compare(
        strategy,
        time_frame=TimeWindow(start, end),
        window_size=CalendarDelta.FIVE_YEARS,
        step_size=CalendarDelta.ONE_YEAR,
    )


def test_performance():
    portfolioA = Portfolio(
        positions={"IWDA.AS": 1},
        strategy=PeriodicContribution(Period.MONTHLY, {"IWDA.AS": 1}),
    )
    portfolioB = Portfolio(
        positions={"XWD.TO": 1},
        strategy=PeriodicContribution(Period.MONTHLY, {"XWD.TO": 1}),
    )
    portfolios = {portfolioA, portfolioB}
    tickers = {ticker for portfolio in portfolios for ticker in portfolio}
    start = datetime.fromisoformat("2000-01-01")
    end = datetime.fromisoformat("2025-01-01")

    # Five Year Performance
    performance = FiveYearPerformanceParameters(
        start=start, end=end, events=global_events, metrics=global_metrics
    ).build(tickers)
    PerformanceReporter.print(performance, portfolios)


def rolling_window_backtrack(
    start, end, window_size, step_size, portfolio
) -> Dict[TimeWindow, TimeSeriesSnapshot]:
    now = time.time()
    backtracker = FlowBacktracker(TimeWindow(start, end), portfolio)
    rolling_window = RollingTimeWindow(start, end, window_size, step_size)
    result = backtracker.rolling_backtrack(rolling_window)

    print(f"Rolling window backtrack time: {time.time() - now}")

    return result


if __name__ == "__main__":
    test_comparison()
