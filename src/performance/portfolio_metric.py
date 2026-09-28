from abc import abstractmethod
from statistics import stdev
from typing import Sequence


from custom_types.time_series_snapshot import TimeSeriesSnapshot


class PortfolioMetric:
    @abstractmethod
    def metric(self, snapshot: TimeSeriesSnapshot) -> float: ...

    def average(self, snapshots: Sequence[TimeSeriesSnapshot]) -> float:
        return sum(map(self.metric, snapshots)) / len(snapshots)


class ReturnMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> float:
        return snapshot.final_value / snapshot.initial_value


class MaxDrawdownMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> float:
        """Pre-condition: series only contains non-negative values."""
        max_value = 0.0
        result = 0.0

        for dp in snapshot.series:
            max_value = max(max_value, dp.value)
            drawdown = (max_value - dp.value) / max_value if max_value > 0.0 else 0.0

            result = max(result, drawdown)

        return result


class VolatilityMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> float:
        if len(snapshot.series) < 2:
            return 0.0

        returns = [
            curr.value / prev.value - 1
            for prev, curr in zip(snapshot.series, snapshot.series[1:])
        ]

        return stdev(returns)


class AnnualizedReturnMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> float:
        if not snapshot.start_timestamp or not snapshot.end_timestamp:
            raise ValueError()
        total_return = ReturnMetric().metric(snapshot)
        days = (snapshot.end_timestamp - snapshot.start_timestamp).days
        return total_return ** (365 / days)
