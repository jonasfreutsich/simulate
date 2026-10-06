from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AllocationStrategy(ABC):

    @abstractmethod
    def reallocate(self, allocation: Dict[str, float]) -> float: ...


@dataclass(frozen=True)
class PeriodicContribution(AllocationStrategy):
    add_allocation: Dict[str, float]

    def reallocate(self, allocation: Dict[str, float]) -> float:
        total = 0.0

        for ticker in allocation:
            amount = self.add_allocation.get(ticker, 0.0)
            allocation[ticker] += amount
            total += amount

        return total


@dataclass(frozen=True)
class Reallocation:
    target_weights: Dict[str, float]

    def reallocate(self, allocation: Dict[str, float]) -> float:
        if allocation.keys() != self.target_weights.keys():
            raise ValueError(
                "Allocation tickers are not the same as configured tickers."
            )

        current_total = sum(allocation.values())

        for ticker in allocation:
            allocation[ticker] = self.target_weights[ticker] * current_total

        return 0.0
