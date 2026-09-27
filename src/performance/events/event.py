from abc import abstractmethod


from custom_types.time_series_snapshot import TimeSeriesSnapshot
from performance.portfolio_metric import MaxDrawDownMetric
from performance.portfolio_metric import VolatilityMetric


class Event:
    @abstractmethod
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool: ...


class CrashEvent(Event):
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        if snapshot.crashed:
            return True
        return False


class NegativeReturnEvent(Event):
    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return snapshot.initial_value > snapshot.final_value


class LimitDrawDownEvent(Event):
    def __init__(self, limit_percent: int):
        self.limit_percent = limit_percent

    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return (MaxDrawDownMetric().metric(snapshot) * 100) > self.limit_percent


class LimitVolatilityEvent(Event):
    def __init__(self, limit_percent: int):
        self.limit_percent = limit_percent

    def filter(self, snapshot: TimeSeriesSnapshot) -> bool:
        return (VolatilityMetric().metric(snapshot) * 100) > self.limit_percent
