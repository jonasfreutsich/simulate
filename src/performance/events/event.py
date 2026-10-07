from abc import abstractmethod
from typing import Dict


from custom_types.custom_types import Percentage
from custom_types.time_series_snapshot import TimeSeriesSnapshot
from performance.portfolio_metric import MaxDrawdownMetric
from performance.portfolio_metric import VolatilityMetric


class PortfolioEvent:
    @abstractmethod
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool: ...


class CrashEvent(PortfolioEvent):
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        if snapshot.crashed:
            return True
        return False


class NegativeReturnEvent(PortfolioEvent):
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return snapshot.initial_value > snapshot.final_value


class LimitDrawdownEvent(PortfolioEvent):
    def __init__(self, limit_percent: Percentage):
        self.limit_percent = limit_percent

    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return MaxDrawdownMetric().metric(snapshot) > self.limit_percent


class LimitVolatilityEvent(PortfolioEvent):
    def __init__(self, limit_percent: Percentage):
        self.limit_percent = limit_percent

    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return VolatilityMetric().metric(snapshot) > self.limit_percent


global_events: Dict[str, "PortfolioEvent"] = {
    "CrashEvent": CrashEvent(),
    "NegativeReturnEvent": NegativeReturnEvent(),
    "10DrawdownEvent": LimitDrawdownEvent(Percentage(0.1)),
    "20DrawdownEvent": LimitDrawdownEvent(Percentage(0.2)),
    "30DrawdownEvent": LimitDrawdownEvent(Percentage(0.3)),
    "10VolatilityEvent": LimitVolatilityEvent(Percentage(0.1)),
    "20VolatilityEvent": LimitVolatilityEvent(Percentage(0.2)),
    "30VolatilityEvent": LimitVolatilityEvent(Percentage(0.3)),
}
