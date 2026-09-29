from dataclasses import dataclass
from datetime import datetime, timedelta

from custom_types.portfolio import Portfolio
from dataseries.data_series import DataSeries


@dataclass
class TimeSeriesSnapshot:
    initial_portfolio: Portfolio
    series: DataSeries
    final_portfolio: Portfolio

    @property
    def initial_value(self) -> float:
        return self.initial_portfolio.get_value()

    @property
    def final_value(self) -> float:
        return self.series[-1].value if self.series else 0.0

    @property
    def return_percentage(self) -> float:
        if self.initial_value == 0:
            return 0.0
        return (self.final_value - self.initial_value) / self.initial_value * 100

    @property
    def crashed(self) -> bool:
        return self.final_portfolio.is_crashed()

    @property
    def start_timestamp(self) -> datetime | None:
        return self.series[0].timestamp if self.series else None

    @property
    def end_timestamp(self) -> datetime | None:
        return self.series[-1].timestamp if self.series else None

    @property
    def duration(self) -> timedelta | None:
        if self.series:
            return self.end_timestamp - self.start_timestamp  # type: ignore[StartAndEndTimestampAreOnlyNoneIfSeriesIsNonEmpty]
        else:
            return None

    def __bool__(self) -> bool:
        return bool(self.series)

    def __len__(self) -> int:
        return len(self.series)
