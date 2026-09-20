# ---------------------------------------------------------------------------
# Brownian motion
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class BrownianMotion(SimulationModel):
    """
    Brownian-motion-style simulation.

    drift:
        Directional movement toward the end value.

    volatility:
        Standard deviation of the random component.
    """

    volatility: float = 1.0
    drift: float = 0.05

    def __post_init__(self) -> None:
        if self.volatility < 0:
            raise ValueError("volatility must be >= 0")

        if self.drift < 0:
            raise ValueError("drift must be >= 0")

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        remaining = max(0.0, 1.0 - context.progress)

        direction = (
            (context.end_value - context.previous_value) * self.drift * remaining
        )

        noise = rng.gauss(0.0, self.volatility)

        return context.previous_value + direction + noise
