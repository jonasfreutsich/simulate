from abc import abstractmethod
from statistics import stdev
from typing import Dict, Sequence, overload


from custom_types.custom_types import Currency, Percentage
from custom_types.time_series_snapshot import TimeSeriesSnapshot


class PortfolioMetric:
    @abstractmethod
    def metric(self, snapshot: TimeSeriesSnapshot) -> Percentage | Currency: ...

    def average(self, snapshots: Sequence[TimeSeriesSnapshot]) -> Percentage | Currency:
        if not snapshots or len(snapshots) == 0:
            raise ValueError()

        total_list = list(map(self.metric, snapshots))
        if isinstance(total_list[0], Currency):
            currency = total_list[0].currency
            return sum(
                total_list,
                Currency(0, currency),
            ) / len(total_list)
        elif isinstance(total_list[0], Percentage):
            return sum(
                total_list,
                Percentage(0),
            ) / len(total_list)
        else:
            raise NotImplemented


class ReturnMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Percentage | Currency:
        return Percentage(
            snapshot.final_value / (snapshot.contributed_value + snapshot.initial_value)
            - 1
        )


class MaxDrawdownMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Percentage:
        """Pre-condition: series only contains non-negative values."""
        max_value = 0.0
        result = 0.0

        for dp in snapshot.series:
            max_value = max(max_value, dp.value)
            drawdown = (max_value - dp.value) / max_value if max_value > 0.0 else 0.0

            result = max(result, drawdown)

        return Percentage(result)


class VolatilityMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Percentage:
        if len(snapshot.series) < 2:
            return Percentage(0.0)

        returns = [
            curr.value / prev.value - 1
            for prev, curr in zip(snapshot.series, snapshot.series[1:])
        ]

        return Percentage(stdev(returns))


class AnnualizedReturnMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Percentage:
        duration = snapshot.duration
        if duration is None:
            raise ValueError("Snapshot duration is invalid")
        if duration.days <= 0:
            raise ValueError("Snapshot duration must be positive")

        total_return = ReturnMetric().metric(snapshot)
        return Percentage((total_return.value + 1) ** (365 / duration.days) - 1)


class AllocationMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Currency:
        return Currency(snapshot.contributed_value, "$")


class FinalValueMetric(PortfolioMetric):
    def metric(self, snapshot: TimeSeriesSnapshot) -> Currency:
        return Currency(snapshot.final_value, "$")


global_metrics: Dict[str, PortfolioMetric] = {
    "ReturnMetric": ReturnMetric(),
    "DrawdownMetric": MaxDrawdownMetric(),
    "VolatilityMetric": VolatilityMetric(),
    "AnnualizedReturnMetric": AnnualizedReturnMetric(),
    "AllocationMetric": AllocationMetric(),
    "FinalValueMetric": FinalValueMetric(),
}
