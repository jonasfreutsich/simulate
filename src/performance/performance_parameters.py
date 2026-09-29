from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Dict, Optional, Set


from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow
from myutils.utils import Utils
from performance.events.event import PortfolioEvent
from performance.portfolio_metric import PortfolioMetric
from performance.portfolio_performance import PortfolioPerformance
from stockdata.stock_data_loader import StockDataLoader


@dataclass
class PerformanceParameters:
    start: datetime
    end: datetime
    window_size: timedelta
    step_size: timedelta
    events: Optional[Dict[str, PortfolioEvent]] = None
    metrics: Optional[Dict[str, PortfolioMetric]] = None

    @property
    def rolling_window(self) -> RollingTimeWindow:
        return RollingTimeWindow(self.start, self.end, self.window_size, self.step_size)

    def performance(
        self, loader: StockDataLoader, portfolios: Set[Portfolio]
    ) -> Dict[Portfolio, Dict[str, float]]:
        if not (self.metrics or self.events):
            raise ValueError(
                "Illegal configuration for PortfolioPerformance. Either metrics or events must be specified."
            )
        metrics = self.metrics or {}
        events = self.events or {}
        intersection = set.intersection(set(events.keys()), set(metrics.keys()))
        if intersection:
            raise ValueError(
                f"Events and Metrics must be named uniquely. Overlap {intersection}."
            )
        return PortfolioPerformance(
            portfolios, self.rolling_window, loader
        ).performance(metrics or {}, events or {})

    def print(
        self, portfolio: Portfolio | Set[Portfolio], loader: StockDataLoader
    ) -> None:
        print(self.__class__.__name__)
        if isinstance(portfolio, Portfolio):
            performance_result = self.performance(loader, {portfolio})
        elif isinstance(portfolio, set):
            performance_result = self.performance(loader, portfolio)
        print(Utils.dict_to_md_table(performance_result))


@dataclass
class FiveYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365 * 5)
    step_size: timedelta = timedelta(days=365)


@dataclass
class TenYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365 * 10)
    step_size: timedelta = timedelta(days=365)


@dataclass
class OneYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365)
    step_size: timedelta = timedelta(days=30)
