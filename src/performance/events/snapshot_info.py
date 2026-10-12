from abc import ABC, abstractmethod

from custom_types.dataseries.snapshot import TimeSeriesSnapshot


class SnapshotInfo(ABC):
    @abstractmethod
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str: ...


class CrashDayInfo(SnapshotInfo):
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str:
        return str(snapshot.end_timestamp)


class StartDayInfo(SnapshotInfo):
    def __call__(self, snapshot: TimeSeriesSnapshot) -> str:
        return str(snapshot.start_timestamp)


global_infos = {"CrashDayInfo": CrashDayInfo(), "StartDayInfo": StartDayInfo()}
