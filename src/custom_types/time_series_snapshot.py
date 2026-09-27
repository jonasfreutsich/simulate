from dataclasses import dataclass
from datetime import datetime
from statistics import stdev

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

    def __bool__(self) -> bool:
        return bool(self.series)

    def __len__(self) -> int:
        return len(self.series)

    def max_drawdown(self) -> float:
        """Pre-condition: series only contains non-negative values."""
        max_value = 0.0
        result = 0.0

        for dp in self.series:
            max_value = max(max_value, dp.value)
            drawdown = (max_value - dp.value) / max_value if max_value > 0.0 else 0.0

            result = max(result, drawdown)

        return result

    def volatility(self) -> float:
        if len(self.series) < 2:
            return 0.0

        returns = [
            curr.value / prev.value - 1
            for prev, curr in zip(self.series, self.series[1:])
        ]

        return stdev(returns)
