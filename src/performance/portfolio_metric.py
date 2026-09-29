from abc import abstractmethod
from statistics import stdev
from typing import Dict, Sequence


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
        duration = snapshot.duration
        if duration is None:
            raise ValueError("Snapshot duration is invalid")
        if duration.days <= 0:
            raise ValueError("Snapshot duration must be positive")

        total_return = ReturnMetric().metric(snapshot)
        return total_return ** (365 / duration.days) - 1


global_metrics: Dict[str, PortfolioMetric] = {
    "ReturnMetric": ReturnMetric(),
    "DrawdownMetric": MaxDrawdownMetric(),
    "VolatilityMetric": VolatilityMetric(),
    "AnnualizedReturnMetric": AnnualizedReturnMetric(),
}
