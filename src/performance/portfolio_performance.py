from dataclasses import dataclass
from turtle import back
from typing import TYPE_CHECKING, Dict, Set, Tuple


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.custom_types import Currency, Percentage
from custom_types.portfolio.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from myutils.utils import Utils
from performance.events.event_processor import EventProcessor

if TYPE_CHECKING:
    from performance.performance_parameters import PerformanceParameters
import logging

logger = logging.getLogger("simulate")


@dataclass(frozen=True)
class PortfolioPerformanceResult:
    metrics: Dict[str, Currency | Percentage]
    events: Dict[str, Currency | Percentage]
    details_info: Dict[TimeWindow, Dict[str, str]]

    @property
    def result_dict(self) -> Dict[str, Currency | Percentage]:
        return {
            **self.metrics,
            **self.events,
        }


class PortfolioPerformance:
    def __init__(
        self,
        parameters: "PerformanceParameters",
        backtracker: FlowBacktracker,
    ):
        self.rolling_window: RollingTimeWindow = parameters.rolling_window.trim(
            backtracker.time_range
        )
        if self.rolling_window.is_empty():
            raise ValueError(
                f"RollingWindow range was narrowed to a trivial RollingWindow while building backtracker."
            )
        self.metrics = parameters.metrics
        self.events = parameters.events
        self.backtracker = backtracker
        self.parameters = parameters
        logger.info(
            f"Built PortfolioPerformance instance:\n\ttickers: {self.backtracker.tickers}\n\ttime range: {self.rolling_window.get_range()}\n\twindow size: {self.rolling_window.window_size}\n\tstep size: {self.rolling_window.step_size}."
        )

    def get_paramters_name(self) -> str:
        return self.parameters.__class__.__name__

    @classmethod
    def build(
        cls,
        tickers: Set[str],
        parameters: "PerformanceParameters",
    ):
        backtracker = FlowBacktracker(
            parameters.rolling_window.get_range(), tickers=tickers
        )
        return cls(parameters, backtracker)

    def evaluate(
        self,
        portfolios: Set[Portfolio],
    ) -> Dict[Portfolio, PortfolioPerformanceResult]:
        event_processor = EventProcessor(self.events)
        return {
            portfolio: self._evaluate_portfolio(portfolio, event_processor)
            for portfolio in portfolios
        }

    def _evaluate_portfolio(
        self,
        portfolio: Portfolio,
        event_processor: EventProcessor,
    ) -> PortfolioPerformanceResult:
        snapshots = self.backtracker.rolling_backtrack(
            self.rolling_window, portfolio=portfolio
        )
        Utils.filter_empty_snapshots(snapshots)
        event_rates = dict(event_processor.evaluate_event_rates(snapshots))
        metric_results = {}
        details_result: Dict[TimeWindow, Dict[str, str]] = {}
        for key, metric in self.metrics.items():
            metric_results[key] = metric.average(tuple(snapshots.values()))
        for window, snapshot in snapshots.items():
            details_result[window] = {}
            for key, metric in self.metrics.items():
                try:
                    details_result[window][key] = str(metric.metric(snapshot))
                except NotImplementedError:
                    continue
        return PortfolioPerformanceResult(metric_results, event_rates, details_result)
