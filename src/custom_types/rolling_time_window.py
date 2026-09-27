from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Any, Generator


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime


class RollingTimeWindow:
    def __init__(
        self,
        start: datetime,
        end: datetime,
        window_size: timedelta,
        step_size: timedelta,
    ):
        self.window_size = window_size
        self.start = start
        self.end = end
        self.step_size = step_size
        if self.step_size <= timedelta(0):
            raise ValueError("step_size must be positive")
        if self.window_size <= timedelta(0):
            raise ValueError("window_size must be positive")

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
            if current_start < timestamp <= current_end:
                yield TimeWindow(start=current_start, end=current_end)
            current_start += self.step_size
