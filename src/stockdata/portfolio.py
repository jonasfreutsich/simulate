from typing import Dict

ZERO_THRESHOLD = 1e-5


class Portfolio:

    def __init__(self, positions: Dict[str, float]) -> None:

        if not positions:
            raise ValueError("Portfolio cannot be empty.")

        if any(value < 0 for value in positions.values()):
            raise ValueError("Positions cannot be negative.")

        if sum(positions.values()) <= ZERO_THRESHOLD:
            raise ValueError("Portfolio value must be positive.")

        self._value = 1
        self._positions = positions
        self._normalize()

    def __str__(self) -> str:
        return str(self._positions)

    def get_value(self) -> float:
        return self._value

    def get_positions(self) -> Dict[str, float]:
        return self._positions.copy()

    def copy(self) -> "Portfolio":
        return Portfolio(self.get_positions())

    def update(self, position_changes: Dict[str, float]) -> None:
        for ticker in self._positions:
            self._positions[ticker] *= position_changes.get(ticker, 1)
        self._normalize()

    def is_crashed(self) -> bool:
        return abs(self.get_value()) < ZERO_THRESHOLD

    def _normalize(self) -> None:
        total = sum(self._positions.values())
        self._value *= total

        self._positions = {
            ticker: value / total for ticker, value in self._positions.items()
        }
