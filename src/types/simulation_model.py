# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------


from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import random


@dataclass(frozen=True, slots=True)
class SimulationConstraints:
    """
    Constraints applied to generated values.

    volatility:
        Magnitude of random noise.

    minimum / maximum:
        Hard value boundaries.

    deviation:
        Maximum distance from the model's target value.

    mean_reversion:
        Pull toward the model target after random noise.

        0.0 = no pull
        1.0 = completely return to target

    clamp:
        If True, values outside minimum/maximum are clamped.
        If False, a ValueError is raised.
    """

    volatility: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    deviation: float | None = None
    mean_reversion: float = 0.0
    clamp: bool = True

    def __post_init__(self) -> None:
        if self.volatility < 0:
            raise ValueError("volatility must be >= 0")

        if self.minimum is not None and self.maximum is not None:
            if self.minimum > self.maximum:
                raise ValueError("minimum must not exceed maximum")

        if self.deviation is not None and self.deviation < 0:
            raise ValueError("deviation must be >= 0")

        if not 0.0 <= self.mean_reversion <= 1.0:
            raise ValueError("mean_reversion must be between 0.0 and 1.0")


# ---------------------------------------------------------------------------
# Simulation context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SimulationContext:
    """
    Information available to a simulation model for every step.
    """

    index: int
    count: int

    timestamp: datetime
    start_time: datetime
    end_time: datetime

    start_value: float
    end_value: float

    previous_value: float

    @property
    def progress(self) -> float:
        """Progress through the simulation, from 0.0 to 1.0."""
        if self.count <= 1:
            return 0.0

        return self.index / (self.count - 1)

    @property
    def elapsed(self) -> timedelta:
        return self.timestamp - self.start_time

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------


class SimulationModel(ABC):
    """
    Base class for all simulation models.

    A model receives the current simulation context and produces
    the next target value.
    """

    @abstractmethod
    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        """
        Return the next model value.

        This value is the underlying signal before generic constraints
        such as volatility and min/max bounds are applied.
        """
        raise NotImplementedError
