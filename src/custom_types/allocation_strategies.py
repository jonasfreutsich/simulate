from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict


@dataclass(frozen=True)
class AllocationStrategy(ABC):

    @abstractmethod
    def reallocate(
        self, allocation: Dict[str, float], passed_time: timedelta
    ) -> float: ...


@dataclass(frozen=True)
class PeriodicContribution(AllocationStrategy):
    contribution: Dict[str, float] | float

    def reallocate(self, allocation: Dict[str, float], passed_time: timedelta) -> float:
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
    pivot_time: timedelta

    def _get_amount(self, ticker: str, passed_time: timedelta) -> float:
        if passed_time < self.pivot_time:
            if isinstance(self.contribution, dict):
                return self.contribution.get(ticker, 0)
            else:
                return self.contribution
        else:
            if isinstance(self.withdraw, dict):
                return -self.withdraw.get(ticker, 0)
            else:
                return -self.withdraw

    def reallocate(self, allocation: Dict[str, float], passed_time: timedelta) -> float:
        total = 0.0

        for ticker in allocation:
            amount = self._get_amount(ticker, passed_time)
            allocation[ticker] += amount
            total += amount

        return total


@dataclass(frozen=True)
class Reallocation(AllocationStrategy):
    target_weights: Dict[str, float]

    def reallocate(self, allocation: Dict[str, float], passed_time: timedelta) -> float:
        if allocation.keys() != self.target_weights.keys():
            raise ValueError(
                "Allocation tickers are not the same as configured tickers."
            )

        current_total = sum(allocation.values())

        for ticker in allocation:
            allocation[ticker] = self.target_weights[ticker] * current_total

        return 0.0
