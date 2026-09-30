from dataclasses import dataclass
from typing import Dict, Set


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow
from myutils.utils import Utils
from performance.events.event import PortfolioEvent
from performance.events.event_processor import EventProcessor
from performance.portfolio_metric import PortfolioMetric
from stockdata.stock_data_loader import StockDataLoader


@dataclass(frozen=True)
class PortfolioPerformanceResult:
    metrics: Dict[str, float]
    events: Dict[str, float]
    num_windows: int

    @property
    def result_dict(self) -> Dict[str, float]:
        return {**self.metrics, **self.events}


class PortfolioPerformance:
    def __init__(self, portfolios, rolling_window, backtracker: FlowBacktracker):
        self.portfolios = portfolios
        self.rolling_window = rolling_window
        self.backtracker = backtracker

    @classmethod
    def build(
        cls,
        portfolios: Set[Portfolio],
        rolling_window: RollingTimeWindow,
        loader: StockDataLoader,
    ):
        tickers = {t for p in portfolios for t in p}
        backtracker = FlowBacktracker(
            loader, rolling_window.get_range(), tickers=tickers
        )
        return cls(portfolios, rolling_window, backtracker)

    def evaluate(
        self, metrics: Dict[str, PortfolioMetric], events: Dict[str, PortfolioEvent]
    ) -> Dict[Portfolio, PortfolioPerformanceResult]:
        event_processor = EventProcessor(events)
        return {
            portfolio: self._evaluate_portfolio(portfolio, metrics, event_processor)
            for portfolio in self.portfolios
        }

    def _evaluate_portfolio(
        self,
        portfolio: Portfolio,
        metrics: Dict[str, PortfolioMetric],
        event_processor: EventProcessor,
    ) -> PortfolioPerformanceResult:
        snap = self.backtracker.rolling_backtrack(
            self.rolling_window, portfolio=portfolio
        )
        Utils.filter_empty_snapshots(snap)
        metric_results = dict(event_processor.evaluate_event_rates(snap))
        event_results = {}
        for key, metric in metrics.items():
            event_results[key] = metric.average(tuple(snap.values()))
        return PortfolioPerformanceResult(metric_results, event_results, len(snap))
