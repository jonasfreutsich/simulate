from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Iterator, Sequence, overload


@dataclass(frozen=True, slots=True)
class DataPoint:
    timestamp: datetime
    value: float


class DataSeries(Sequence[DataPoint]):
    """Time-indexed series of floating-point values."""

    def __init__(self, points: Iterable[tuple[datetime, float] | DataPoint] = ()):
        normalized = [p if isinstance(p, DataPoint) else DataPoint(*p) for p in points]

        normalized.sort(key=lambda p: p.timestamp)

        # A series has at most one value for a given timestamp
        for a, b in zip(normalized, normalized[1:]):
            if a.timestamp == b.timestamp:
                raise ValueError(f"Duplicate timestamp: {a.timestamp}")

        self._points = tuple(normalized)
        self._timestamps = tuple(p.timestamp for p in self._points)

    def __len__(self) -> int:
        return len(self._points)

    @overload
    def __getitem__(self, index: int) -> DataPoint: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[DataPoint, ...]: ...

    def __getitem__(self, index: int | slice) -> DataPoint | tuple[DataPoint, ...]:
        return self._points[index]

    def __iter__(self) -> Iterator[DataPoint]:
        return iter(self._points)

    def value_at(self, timestamp: datetime) -> float:
        """Return the value at an exact timestamp."""
        i = bisect_left(self._timestamps, timestamp)

        if i == len(self._points) or self._timestamps[i] != timestamp:
            raise KeyError(timestamp)

        return self._points[i].value

    def before(self, timestamp: datetime) -> DataPoint | None:
        """Return the last observation at or before timestamp."""
        i = bisect_right(self._timestamps, timestamp)

        return self._points[i - 1] if i else None

    def after(self, timestamp: datetime) -> DataPoint | None:
        """Return the first observation at or after timestamp."""
        i = bisect_left(self._timestamps, timestamp)

        return self._points[i] if i < len(self._points) else None

    def between(
        self,
        start: datetime,
        end: datetime,
    ) -> "DataSeries":
        """Return observations in [start, end]."""
        if start > end:
            raise ValueError("start must not be after end")

        left = bisect_left(self._timestamps, start)
        right = bisect_right(self._timestamps, end)

        return DataSeries(self._points[left:right])

    def start(self) -> DataPoint:
        return self._points[0]

    def end(self) -> DataPoint:
        return self._points[-1]

    def timeline(self) -> Sequence[datetime]:
        return tuple(sorted(point.timestamp for point in self._points))

    @staticmethod
    def common_timeline(series: Iterable["DataSeries"]) -> Sequence[datetime]:
        if not series:
            return ()

        timelines = [set(data.timeline()) for data in series]
        common = set.intersection(*timelines)

        return tuple(sorted(common))
