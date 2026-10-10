from datetime import datetime
from typing import Dict, Iterator, Optional

from custom_types.allocation.allocation_strategies import AllocationStrategy
from custom_types.allocation.allocator import AllocationSchedule
from custom_types.dataseries.data_series import DataSeries

ZERO_THRESHOLD = 1e-5


class Portfolio:

    def __init__(
        self,
        positions: Dict[str, float],
        strategy: Optional[AllocationStrategy] = None,
    ) -> None:

        if not positions:
            raise ValueError("Portfolio cannot be empty.")

        if any(value <= 0 for value in positions.values()):
            raise ValueError("Positions cannot be non-positive.")

        if sum(positions.values()) <= ZERO_THRESHOLD:
            raise ValueError("Portfolio value must be positive.")

        self._positions: Dict[str, float] = positions
        self._allocator: AllocationSchedule | None = (
            AllocationSchedule(strategy) if strategy is not None else None
        )

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        repr = tuple(
            ticker + "=" + str(value) for ticker, value in self._positions.items()
        )
        allocator_repr = (
            "" if self._allocator is None else str(self._allocator.strategy)
        )
        return f"Portfolio{repr}\n" + allocator_repr

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Portfolio):
            return NotImplemented
        if self._positions.keys() != other._positions.keys():
            return False
        for key in self._positions:
            if abs(self._positions[key] - other._positions[key]) >= ZERO_THRESHOLD:
                return False
        return True

    def __contains__(self, item: str) -> bool:
        if isinstance(item, str):
            return item in self._positions
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        return iter(self._positions)

    def get_value(self) -> float:
        return sum(self._positions.values())

    def get_total_contributions(self) -> float:
        return self._allocator.total_contributions if self._allocator else 0.0

    def get_total_withdrawls(self) -> float:
        return self._allocator.total_withdrawls if self._allocator else 0.0

    def get_positions(self) -> Dict[str, float]:
        return self._positions.copy()

    def copy(self) -> "Portfolio":
        return Portfolio(
            self.get_positions(),
            self._allocator.strategy if self._allocator is not None else None,
        )

    def flow(
        self,
        position_changes: Dict[str, float] | Dict[str, DataSeries],
        timestamp: datetime,
    ) -> None:
        for ticker in self._positions:
            change = position_changes.get(
                ticker, 1.0
            )  # Default to no change if not specified
            if isinstance(change, DataSeries):
                for datapoint in change:
                    self._positions[ticker] *= datapoint.value
            elif isinstance(change, float):
                self._positions[ticker] *= change
            else:
                raise ValueError(
                    f"Invalid type for position change: {type(change)}. Must be float or DataSeries."
                )
        if self._allocator is not None:
            self._allocator.apply(self._positions, timestamp)

    def is_crashed(self) -> bool:
        return self.get_value() < ZERO_THRESHOLD

    def normalize(self) -> "Portfolio":
        total = self.get_value()

        return Portfolio(
            {ticker: value / total for ticker, value in self._positions.items()}
        )
