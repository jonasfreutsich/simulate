from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import Dict, Set


from custom_types.rolling_time_window import RollingTimeWindow
from performance.events.event import PortfolioEvent
from performance.portfolio_metric import PortfolioMetric
from performance.portfolio_performance import (
    PortfolioPerformance,
)
from stockdata.stock_data_loader import StockDataLoader


@dataclass(frozen=True)
class PerformanceParameters:
    start: datetime
    end: datetime
    window_size: timedelta
    step_size: timedelta
    events: Dict[str, PortfolioEvent] = field(default_factory=dict)
    metrics: Dict[str, PortfolioMetric] = field(default_factory=dict)

    def __poist_init__(self):
        if not self.metrics and not self.events:
            raise ValueError("Either metrics or events must be specified.")
        overlap = set(self.events) & set(self.metrics)
        if overlap:
            raise ValueError(
                f"Events and Metrics keys must be unique. Overlap: {overlap}."
            )

    @property
    def rolling_window(self) -> RollingTimeWindow:
        return RollingTimeWindow(self.start, self.end, self.window_size, self.step_size)

    def build(self, loader: StockDataLoader, tickers: Set[str]) -> PortfolioPerformance:
        return PortfolioPerformance.build(loader, tickers, self)


@dataclass(frozen=True)
class FiveYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365 * 5)
    step_size: timedelta = timedelta(days=365)


@dataclass(frozen=True)
class TenYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365 * 10)
    step_size: timedelta = timedelta(days=365)


@dataclass(frozen=True)
class OneYearPerformanceParameters(PerformanceParameters):
    window_size: timedelta = timedelta(days=365)
    step_size: timedelta = timedelta(days=30)
