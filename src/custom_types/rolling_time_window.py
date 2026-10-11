from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generator


from custom_types.time_types import CalendarDelta


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.start, datetime) or not isinstance(self.end, datetime):
            raise ValueError("start and end must be datetime instances.")
        if self.start >= self.end:
            raise ValueError("start must be before end.")

    def __contains__(self, value) -> bool:
        if isinstance(value, datetime):
            return self.start <= value < self.end

        if isinstance(value, TimeWindow):
            return self.start <= value.start and value.end <= self.end

        return False

    def __repr__(self) -> str:
        fmt = "%Y-%m-%d"
        return "TimeRange" + str([self.start.strftime(fmt), self.end.strftime(fmt)])

    def __str__(self) -> str:
        return repr(self)

    def __hash__(self) -> int:
        return hash(repr(self))


class RollingTimeWindow:
    def __init__(
        self,
        start: datetime,
        end: datetime,
        window_size: CalendarDelta,
        step_size: CalendarDelta,
    ):
        self.window_size = window_size
        self.start = start
        self.end = end
        self.step_size = step_size

    def __iter__(self) -> Generator[TimeWindow, Any, None]:
        current_start = self.start
        while current_start + self.window_size <= self.end:
            current_end = current_start + self.window_size
            yield TimeWindow(start=current_start, end=current_end)
            current_start += self.step_size

    def affected_windows(self, timestamp: datetime) -> Generator[TimeWindow, Any, None]:
        current_start = self.start
        while current_start + self.window_size <= self.end:
            current_end = current_start + self.window_size
            if current_start <= timestamp < current_end:
                yield TimeWindow(start=current_start, end=current_end)
            current_start += self.step_size

    def get_range(self) -> TimeWindow:
        return TimeWindow(self.start, self.end)

    def is_empty(self) -> bool:
        return self.start + self.window_size > self.end

    def trim(self, range: TimeWindow) -> "RollingTimeWindow":
        if not range in self.get_range():
            raise ValueError("Cannot trim a RollingTimeWindow to a larger range.")
        return RollingTimeWindow(
            range.start, range.end, self.window_size, self.step_size
        )
