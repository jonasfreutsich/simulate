from typing import Dict

from dataseries.data_series import DataSeries

ZERO_THRESHOLD = 1e-5


class Portfolio:

    def __init__(self, positions: Dict[str, float]) -> None:

        if not positions:
            raise ValueError("Portfolio cannot be empty.")

        if any(value <= 0 for value in positions.values()):
            raise ValueError("Positions cannot be non-positive.")

        if sum(positions.values()) <= ZERO_THRESHOLD:
            raise ValueError("Portfolio value must be positive.")

        self._positions = positions

    def __str__(self) -> str:
        return str(self._positions)

    def __repr__(self) -> str:
        return f"Portfolio(positions={self._positions})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Portfolio):
            return NotImplemented
        if self._positions.keys() != other._positions.keys():
            return False
        for key in self._positions:
            if abs(self._positions[key] - other._positions[key]) >= ZERO_THRESHOLD:
                return False
        return True

    def get_value(self) -> float:
        return sum(self._positions.values())

    def get_positions(self) -> Dict[str, float]:
        return self._positions.copy()

    def copy(self) -> "Portfolio":
        return Portfolio(self.get_positions())

    def flow(self, position_changes: Dict[str, float] | Dict[str, DataSeries]) -> None:
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

    def is_crashed(self) -> bool:
        return abs(self.get_value()) < ZERO_THRESHOLD

    def normalize(self) -> "Portfolio":
        total = self.get_value()

        return Portfolio(
            {ticker: value / total for ticker, value in self._positions.items()}
        )
