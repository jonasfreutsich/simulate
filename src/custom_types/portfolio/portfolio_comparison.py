from typing import Set

from custom_types.allocation.allocation_strategies import AllocationStrategy
from custom_types.time_types import CalendarDelta
from custom_types.portfolio.portfolio import Portfolio
from custom_types.rolling_time_window import TimeWindow
from performance.performance_parameters import PerformanceParameters
from performance.performance_reporter import PerformanceReporter

from performance.portfolio_metric import (
    global_metrics,
)

from performance.events.event import global_events


class PortfolioComparison:

    def __init__(self, portfolios: Set[Portfolio]):
        self.portfolios = portfolios.copy()
        self.events = global_events
        self.metrics = global_metrics

    def compare(
        self,
        strategy: AllocationStrategy,
        time_frame: TimeWindow,
        window_size: CalendarDelta,
        step_size: CalendarDelta,
    ):
        portfolios = {
            Portfolio(portfolio.get_positions(), strategy)
            for portfolio in self.portfolios
        }
        tickers = {ticker for portfolio in portfolios for ticker in portfolio}
        start = time_frame.start
        end = time_frame.end

        # Performance
        performance = PerformanceParameters(
            start=start,
            end=end,
            window_size=window_size,
            step_size=step_size,
            events=self.events,
            metrics=self.metrics,
        ).build(tickers)
        PerformanceReporter.save("results.md", performance, portfolios, details=False)
