from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set


from custom_types.time_types import CalendarDelta
from custom_types.rolling_time_window import RollingTimeWindow
from performance.events.event import PortfolioEvent
from performance.portfolio_metric import PortfolioMetric
from performance.portfolio_performance import (
    PortfolioPerformance,
)


@dataclass(frozen=True)
class PerformanceParameters:
    start: datetime
    end: datetime
    window_size: CalendarDelta
    step_size: CalendarDelta
    events: Dict[str, PortfolioEvent] = field(default_factory=dict)
    metrics: Dict[str, PortfolioMetric] = field(default_factory=dict)

    def __post_init__(self):
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

    def build(self, tickers: Set[str]) -> PortfolioPerformance:
        return PortfolioPerformance.build(tickers, self)


@dataclass(frozen=True)
class FiveYearPerformanceParameters(PerformanceParameters):
    window_size: CalendarDelta = CalendarDelta.FIVE_YEARS
    step_size: CalendarDelta = CalendarDelta.ONE_YEAR


@dataclass(frozen=True)
class TenYearPerformanceParameters(PerformanceParameters):
    window_size: CalendarDelta = CalendarDelta.TEN_YEARS
    step_size: CalendarDelta = CalendarDelta.ONE_YEAR


@dataclass(frozen=True)
class OneYearPerformanceParameters(PerformanceParameters):
    window_size: CalendarDelta = CalendarDelta.FIVE_YEARS
    step_size: CalendarDelta = CalendarDelta.ONE_YEAR


@dataclass(frozen=True)
class OneYearMonthlyGrainPerformanceParameters(PerformanceParameters):
    window_size: CalendarDelta = CalendarDelta.FIVE_YEARS
    step_size: CalendarDelta = CalendarDelta.ONE_YEAR
