from abc import ABC, abstractmethod

from custom_types.dataseries.snapshot import TimeSeriesSnapshot
from performance.events.event import CrashEvent


class SnapshotInfo(ABC):
    @abstractmethod
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str: ...


class CrashDayInfo(SnapshotInfo):
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str:
        if CrashEvent().filter(snapshot):
            return str(snapshot.end_timestamp)
        else:
            return " not crashed "


class StartDayInfo(SnapshotInfo):
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str:
        return str(snapshot.start_timestamp)


global_infos = {"CrashDayInfo": CrashDayInfo(), "StartDayInfo": StartDayInfo()}
