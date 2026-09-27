from abc import abstractmethod


from custom_types.time_series_snapshot import TimeSeriesSnapshot


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
