from typing import Dict


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import RollingTimeWindow
from performance.events.event import PortfolioEvent
from performance.events.event_processor import EventProcessor
from performance.portfolio_metric import PortfolioMetric
from stockdata.stock_data_loader import StockDataLoader


class PortfolioPerformance:
    def __init__(
        self,
        portfolio: Portfolio,
        rolling_window: RollingTimeWindow,
        loader: StockDataLoader,
    ):
        self.portfolio = portfolio
        self.rolling_window = rolling_window
        self.snapshots = FlowBacktracker(
            loader,
            self.rolling_window.start,
            self.rolling_window.end,
            list(self.portfolio.get_positions().keys()),
        ).rolling_backtrack(portfolio, rolling_window)

    def performance(
        self, metrics: Dict[str, PortfolioMetric], events: Dict[str, PortfolioEvent]
    ) -> Dict[str, float]:
        """Validation of metrics and events must be ensured by caller: Not both empty and no duplicate keys."""
        event_processor = EventProcessor(events)
        results = event_processor.evaluate_event_rates(self.snapshots)

        for key, metric in metrics.items():
            results[key] = metric.average(tuple(self.snapshots.values()))

        return results
