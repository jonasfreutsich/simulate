from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from matplotlib.dates import relativedelta

from custom_types.time_types import Period


@dataclass(frozen=True)
class AllocationStrategy(ABC):
    period: Period

    @abstractmethod
    def reallocate(
        self, allocation: Dict[str, float], start_time: datetime, current_time: datetime
    ) -> float: ...


@dataclass(frozen=True)
class PeriodicContribution(AllocationStrategy):
    contribution: Dict[str, float] | float

    def reallocate(
        self, allocation: Dict[str, float], start_time: datetime, current_time: datetime
    ) -> float:
        total = 0.0

        for ticker in allocation:
            amount = (
                self.contribution.get(ticker, 0.0)
                if isinstance(self.contribution, dict)
                else self.contribution
            )
            allocation[ticker] += amount
            total += amount

        return total


@dataclass(frozen=True)
class FireStrategy(AllocationStrategy):
    contribution: Dict[str, float] | float
    withdraw: Dict[str, float] | float
    pivot: relativedelta

    def _get_amount(
        self, ticker: str, start_time: datetime, current_time: datetime
    ) -> float:
        if current_time < start_time + self.pivot:
            if isinstance(self.contribution, dict):
                return self.contribution.get(ticker, 0)
            else:
                return self.contribution
        else:
            if isinstance(self.withdraw, dict):
                return -self.withdraw.get(ticker, 0)
            else:
                return -self.withdraw

    def reallocate(
        self, allocation: Dict[str, float], start_time: datetime, current_time: datetime
    ) -> float:
        total = 0.0

        for ticker in allocation:
            amount = self._get_amount(ticker, start_time, current_time)
            allocation[ticker] += amount
            total += amount

        return total


@dataclass(frozen=True)
class Reallocation(AllocationStrategy):
    target_weights: Dict[str, float]

    def reallocate(
        self, allocation: Dict[str, float], start_time: datetime, current_time: datetime
    ) -> float:
        if allocation.keys() != self.target_weights.keys():
            raise ValueError(
                "Allocation tickers are not the same as configured tickers."
            )

        current_total = sum(allocation.values())

        for ticker in allocation:
            allocation[ticker] = self.target_weights[ticker] * current_total

        return 0.0
