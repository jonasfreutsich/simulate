from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Set


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.custom_types import Currency, Percentage
from custom_types.portfolio.portfolio import Portfolio
from myutils.utils import Utils
from performance.events.event_processor import EventProcessor

if TYPE_CHECKING:
    from performance.performance_parameters import PerformanceParameters
from stockdata.stock_data_loader import StockDataLoader


@dataclass(frozen=True)
class PortfolioPerformanceResult:
    metrics: Dict[str, Currency | Percentage]
    events: Dict[str, Currency | Percentage]
    num_windows: int

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
        self.rolling_window = parameters.rolling_window
        self.metrics = parameters.metrics
        self.events = parameters.events
        self.backtracker = backtracker
        self.parameters = parameters

    def get_paramters_name(self) -> str:
        return self.parameters.__class__.__name__

    @classmethod
    def build(
        cls,
        loader: StockDataLoader,
        tickers: Set[str],
        parameters: "PerformanceParameters",
    ):
        backtracker = FlowBacktracker(
            loader, parameters.rolling_window.get_range(), tickers=tickers
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
        snap = self.backtracker.rolling_backtrack(
            self.rolling_window, portfolio=portfolio
        )
        Utils.filter_empty_snapshots(snap)
        metric_results = dict(event_processor.evaluate_event_rates(snap))
        event_results = {}
        for key, metric in self.metrics.items():
            event_results[key] = metric.average(tuple(snap.values()))
        return PortfolioPerformanceResult(metric_results, event_results, len(snap))
