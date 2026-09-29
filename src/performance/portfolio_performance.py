from typing import Dict, Set


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow
from myutils.utils import Utils
from performance.events.event import PortfolioEvent
from performance.events.event_processor import EventProcessor
from performance.portfolio_metric import PortfolioMetric
from stockdata.stock_data_loader import StockDataLoader


class PortfolioPerformance:
    def __init__(
        self,
        portfolios: Set[Portfolio],
        rolling_window: RollingTimeWindow,
        loader: StockDataLoader,
    ):
        tickers = set(ticker for portfolio in portfolios for ticker in portfolio)
        self.backtracker = FlowBacktracker(
            loader,
            rolling_window.get_range(),
            tickers=tickers,
        )
        self.portfolios = portfolios
        self.rolling_window = rolling_window

    def performance(
        self, metrics: Dict[str, PortfolioMetric], events: Dict[str, PortfolioEvent]
    ) -> Dict[Portfolio, Dict[str, float]]:
        """Validation of metrics and events must be ensured by caller: Not both empty and no duplicate keys."""
        event_processor = EventProcessor(events)
        results: Dict[Portfolio, Dict[str, float]] = {}
        for portfolio in self.portfolios:
            snap = self.backtracker.rolling_backtrack(
                self.rolling_window, portfolio=portfolio
            )
            Utils.filter_empty_snapshots(snap)
            event_rates = event_processor.evaluate_event_rates(snap)
            results[portfolio] = event_rates

            for key, metric in metrics.items():
                results[portfolio][key] = metric.average(tuple(snap.values()))

        return results
