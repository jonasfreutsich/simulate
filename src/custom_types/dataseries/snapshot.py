from dataclasses import dataclass
from datetime import datetime, timedelta

from custom_types.portfolio.portfolio import Portfolio
from custom_types.dataseries.data_series import DataSeries


@dataclass
class TimeSeriesSnapshot:
    initial_portfolio: Portfolio
    series: DataSeries
    final_portfolio: Portfolio

    @property
    def initial_value(self) -> float:
        return self.initial_portfolio.get_value()

    @property
    def contributed_value(self) -> float:
        return self.final_portfolio.get_total_contributions()

    @property
    def withdrawl_value(self) -> float:
        return self.final_portfolio.get_total_withdrawls()

    @property
    def final_value(self) -> float:
        return self.final_portfolio.get_value()

    @property
    def total_interest(self) -> float:
        return (
            self.final_value
            - self.initial_value
            - self.contributed_value
            + self.withdrawl_value
        )

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
