from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Dict, Optional

from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow
from performance.events.event import PortfolioEvent
from performance.portfolio_metric import PortfolioMetric
from performance.portfolio_performance import PortfolioPerformance
from stockdata.stock_data_loader import StockDataLoader


@dataclass
class PerformanceParameters:
    portfolio: Portfolio
    start: datetime
    end: datetime
    window_size: timedelta
    step_size: timedelta
    events: Optional[Dict[str, PortfolioEvent]] = None
    metrics: Optional[Dict[str, PortfolioMetric]] = None

    @property
    def rolling_window(self) -> RollingTimeWindow:
        return RollingTimeWindow(self.start, self.end, self.window_size, self.step_size)

    def performance(self, loader: StockDataLoader) -> Dict[str, float]:
        if not (self.metrics or self.events):
            raise ValueError(
                "Illegal configuration for PortfolioPerformance. Either metrics or events must be specified."
            )
        metrics = self.metrics or {}
        events = self.events or {}
        if set.intersection(set(metrics.keys()), set(metrics.keys())):
            raise ValueError("Events and Metrics must be named uniquely.")
        return PortfolioPerformance(
            self.portfolio, self.rolling_window, loader
        ).performance(metrics or {}, events or {})
